from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from typing import List, Optional, Dict, Any
from decimal import Decimal, ROUND_UP

from db_connection import engine
from models import Part, Brand, Category, SupplierPrice, Warehouse, FxRate, PricingRule

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/parts", tags=["parts-public"])


def _get_fx_rate_pln(db: Session, from_currency: str) -> Optional[Decimal]:
    if not from_currency or from_currency.upper() == "PLN":
        return Decimal("1")
    rate = (
        db.query(FxRate)
        .filter(FxRate.from_currency == from_currency.upper(), FxRate.to_currency == "PLN")
        .order_by(FxRate.updated_at.desc())
        .first()
    )
    return Decimal(str(rate.rate)) if rate else None


def _availability_status(available_qty: int, stock_status: str) -> str:
    status = (stock_status or "").upper()
    if available_qty and available_qty > 0 and status in {"IN_STOCK", "AVAILABLE", "LOW_STOCK"}:
        return "Available"
    if status in {"BACKORDER", "PREORDER"}:
        return "On order"
    return "Unavailable"


def _choose_best_offer(db: Session, part: Part) -> Optional[Dict[str, Any]]:
    prices: List[SupplierPrice] = db.query(SupplierPrice).filter(SupplierPrice.part_id == part.id).all()
    if not prices:
        return None

    offers: List[Dict[str, Any]] = []
    for sp in prices:
        wh = db.query(Warehouse).filter(Warehouse.id == sp.warehouse_id).first()
        fx = _get_fx_rate_pln(db, sp.currency)
        if fx is None:
            continue
        cost_pln = (Decimal(str(sp.base_price)) * fx).quantize(Decimal("0.01"))
        offers.append(
            {
                "supplier_price": sp,
                "warehouse": wh,
                "cost_pln": cost_pln,
                "availability_status": _availability_status(sp.available_qty, sp.stock_status),
                "lead_time_days": sp.lead_time_days if sp.lead_time_days is not None else (wh.default_lead_time_days if wh else 0),
            }
        )

    if not offers:
        return None

    def sort_key(o: Dict[str, Any]):
        region = (o.get("warehouse").region if o.get("warehouse") else "").upper()
        prefer = 0 if region == "EU" else 1
        return (prefer, o["cost_pln"], o["lead_time_days"]) 

    offers.sort(key=sort_key)
    return offers[0]


def _apply_pricing_rule(db: Session, part: Part, offer: Dict[str, Any]) -> Decimal:
    cost = offer["cost_pln"]
    region = (offer.get("warehouse").region if offer.get("warehouse") else None)
    supplier_id = offer["supplier_price"].supplier_id

    q = (
        db.query(PricingRule)
        .filter(
            PricingRule.is_active == True,  
            PricingRule.price_min <= cost,
            PricingRule.price_max >= cost,
            PricingRule.warehouse_region == region,
        )
        .order_by(PricingRule.priority.asc())
    )

    rules = q.all()
    def rule_matches(r: PricingRule) -> bool:
        if r.brand_id is not None and r.brand_id != part.brand_id:
            return False
        if r.category_id is not None and r.category_id != part.category_id:
            return False
        if r.supplier_id is not None and r.supplier_id != supplier_id:
            return False
        return True

    chosen = next((r for r in rules if rule_matches(r)), None)
    if not chosen:
        selling = (cost * Decimal("1.25")).quantize(Decimal("1"), rounding=ROUND_UP)
        return selling

    margin = Decimal(str(chosen.margin_percent)) / Decimal("100")
    fixed = Decimal(str(chosen.fixed_markup))
    price = cost * (Decimal("1") + margin) + fixed
    return price.quantize(Decimal("1"), rounding=ROUND_UP)


@router.get("/search")
# Public: search parts with pricing & availability
def search_parts(
    q: Optional[str] = Query(None, min_length=1, description="Free-text search"),
    brand: Optional[str] = Query(None, min_length=1, description="Brand name filter"),
    category: Optional[str] = Query(None, min_length=1, description="Category name filter"),
    vehicle: Optional[str] = Query(None, min_length=1, description="Vehicle YMM filter (simple contains)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Part)

    if q:
        like = f"%{q}%"
        query = query.filter(
            (Part.part_number.ilike(like))
            | (Part.normalized_part_number.ilike(like))
            | (Part.name.ilike(like))
            | (Part.description.ilike(like))
        )

    if brand:
        query = query.join(Brand, Brand.id == Part.brand_id).filter(Brand.name.ilike(f"%{brand}%"))

    if category:
        query = query.join(Category, Category.id == Part.category_id).filter(Category.name.ilike(f"%{category}%"))

    parts = query.offset(skip).limit(limit).all()

    results: List[Dict[str, Any]] = []
    for p in parts:
        brand_obj = db.query(Brand).filter(Brand.id == p.brand_id).first()
        offer = _choose_best_offer(db, p)
        if offer:
            selling = _apply_pricing_rule(db, p, offer)
            availability = offer["availability_status"]
            lead_time = offer["lead_time_days"]
        else:
            selling = None
            availability = "Unavailable"
            lead_time = None

        results.append(
            {
                "id": p.id,
                "name": p.name,
                "brand": brand_obj.name if brand_obj else None,
                "part_number": p.part_number,
                "selling_price": str(selling) if selling is not None else None,
                "currency": "PLN" if selling is not None else None,
                "availability_status": availability,
                "estimated_lead_time_days": lead_time,
                "thumbnail_image": (p.images[0] if p.images else None),
            }
        )

    return results


@router.get("/{part_id}")
# Public: get part detail with offer & delivery estimate
def get_part_detail(
    part_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    brand_obj = db.query(Brand).filter(Brand.id == part.brand_id).first()

    offer = _choose_best_offer(db, part)
    if offer:
        selling = _apply_pricing_rule(db, part, offer)
        availability = offer["availability_status"]
        lead_time = offer["lead_time_days"]
        min_days = (lead_time or 0) + 2
        max_days = (lead_time or 0) + 5
        delivery_range = f"{min_days}–{max_days} days"
    else:
        selling = None
        availability = "Unavailable"
        lead_time = None
        delivery_range = None

    return {
        "id": part.id,
        "name": part.name,
        "brand": brand_obj.name if brand_obj else None,
        "part_number": part.part_number,
        "normalized_part_number": part.normalized_part_number,
        "description": part.description,
        "category_id": part.category_id,
        "subcategory_id": part.subcategory_id,
        "images": part.images,
        "attributes": part.attributes,
        "vehicle_fitment": part.vehicle_fitment,
        "selling_price": str(selling) if selling is not None else None,
        "currency": "PLN" if selling is not None else None,
        "availability_status": availability,
        "estimated_delivery_range": delivery_range,
    }
