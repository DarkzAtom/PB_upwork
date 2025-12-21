from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from typing import List, Optional, Dict, Any
from decimal import Decimal, ROUND_UP

from app.parts.parts_model import Part
from app.brands.brands_model import Brand
from app.categories.categories_model import Category
from app.subcategories.subcategories_model import Subcategory
from app.supplier_price.supplier_price_model import SupplierPrice
from app.warehouses.warehouses_model import Warehouse
from app.fx_rates.fx_rates_model import FxRate
from app.pricing_rules.pricing_rules_model import PricingRule
from app.parts.parts_schema import (
    PartCreate,
    PartUpdate,
    PartResponse,
    PartAdmin,
)

from db_routers_connection import get_db


router = APIRouter(prefix="/api/parts/admin", tags=["parts-admin"])


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


def _best_cost_pln(db: Session, part_id: int) -> Optional[Decimal]:
    prices: List[SupplierPrice] = db.query(SupplierPrice).filter(SupplierPrice.part_id == part_id).all()
    best: Optional[Decimal] = None
    for sp in prices:
        fx = _get_fx_rate_pln(db, sp.currency)
        if fx is None:
            continue
        cost = (Decimal(str(sp.base_price)) * fx).quantize(Decimal("0.01"))
        if best is None or cost < best:
            best = cost
    return best


@router.get("", response_model=List[PartResponse])
# Admin: list parts with optional filters
def list_parts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    supplier_id: Optional[int] = Query(None, gt=0),
    category_id: Optional[int] = Query(None, gt=0),
    db: Session = Depends(get_db),
):
    query = db.query(Part)

    if category_id:
        query = query.filter(Part.category_id == category_id)

    if supplier_id:
        part_ids_q = db.query(SupplierPrice.part_id).filter(SupplierPrice.supplier_id == supplier_id).distinct()
        query = query.filter(Part.id.in_(part_ids_q))

    parts = query.offset(skip).limit(limit).all()
    return parts


@router.post("", response_model=PartResponse, status_code=201)
# Admin: create part
def create_part(part: PartCreate, db: Session = Depends(get_db)):
    if not db.query(Brand.id).filter(Brand.id == part.brand_id).first():
        raise HTTPException(status_code=404, detail="Brand not found")
    if not db.query(Category.id).filter(Category.id == part.category_id).first():
        raise HTTPException(status_code=404, detail="Category not found")
    if not db.query(Subcategory.id).filter(Subcategory.id == part.subcategory_id).first():
        raise HTTPException(status_code=404, detail="Subcategory not found")

    exists = (
        db.query(Part.id)
        .filter(Part.brand_id == part.brand_id, Part.normalized_part_number == part.normalized_part_number)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Part with this brand and normalized_part_number already exists")

    db_part = Part(**part.dict())
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part


@router.get("/{part_id}", response_model=PartAdmin)
# Admin: get part detail (admin view)
def get_part_admin(part_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    p = db.query(Part).filter(Part.id == part_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Part not found")

    brand = db.query(Brand).filter(Brand.id == p.brand_id).first()
    sp = db.query(SupplierPrice).filter(SupplierPrice.part_id == p.id).first()
    best_cost = _best_cost_pln(db, p.id)

    return PartAdmin(
        id=p.id,
        part_number=p.part_number,
        name=p.name,
        brand=brand.name if brand else None,
        supplier_id=(sp.supplier_id if sp else None),
        cost_price=(best_cost if best_cost is not None else None),
        margin_percent=None,
        selling_price=None,
        availability=None,
    )


@router.put("/{part_id}", response_model=PartResponse)
# Admin: update part
def update_part(part_id: int = Path(..., gt=0), part_update: PartUpdate = None, db: Session = Depends(get_db)):
    db_part = db.query(Part).filter(Part.id == part_id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="Part not found")

    data = part_update.dict(exclude_unset=True)

    if "brand_id" in data and not db.query(Brand.id).filter(Brand.id == data["brand_id"]).first():
        raise HTTPException(status_code=404, detail="Brand not found")
    if "category_id" in data and not db.query(Category.id).filter(Category.id == data["category_id"]).first():
        raise HTTPException(status_code=404, detail="Category not found")
    if "subcategory_id" in data and not db.query(Subcategory.id).filter(Subcategory.id == data["subcategory_id"]).first():
        raise HTTPException(status_code=404, detail="Subcategory not found")

    new_brand_id = data.get("brand_id", db_part.brand_id)
    new_norm = data.get("normalized_part_number", db_part.normalized_part_number)
    conflict = (
        db.query(Part.id)
        .filter(
            Part.id != db_part.id,
            Part.brand_id == new_brand_id,
            Part.normalized_part_number == new_norm,
        )
        .first()
    )
    if conflict:
        raise HTTPException(status_code=409, detail="Part with this brand and normalized_part_number already exists")

    for k, v in data.items():
        setattr(db_part, k, v)

    db.commit()
    db.refresh(db_part)
    return db_part


@router.delete("/{part_id}", status_code=204)
# Admin: delete part
def delete_part(part_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    db_part = db.query(Part).filter(Part.id == part_id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="Part not found")
    db.delete(db_part)
    db.commit()
    return None


@router.post("/bulk-create")
# Admin: bulk create parts
def bulk_create_parts(parts_data: List[PartCreate], db: Session = Depends(get_db)):
    created = 0
    failed = 0
    errors: List[str] = []
    to_insert: List[Part] = []

    for idx, pdata in enumerate(parts_data):
        try:
            if not db.query(Brand.id).filter(Brand.id == pdata.brand_id).first():
                raise ValueError(f"Row {idx}: Brand {pdata.brand_id} not found")
            if not db.query(Category.id).filter(Category.id == pdata.category_id).first():
                raise ValueError(f"Row {idx}: Category {pdata.category_id} not found")
            if not db.query(Subcategory.id).filter(Subcategory.id == pdata.subcategory_id).first():
                raise ValueError(f"Row {idx}: Subcategory {pdata.subcategory_id} not found")

            exists = (
                db.query(Part.id)
                .filter(Part.brand_id == pdata.brand_id, Part.normalized_part_number == pdata.normalized_part_number)
                .first()
            )
            if exists:
                raise ValueError(
                    f"Row {idx}: Part with brand {pdata.brand_id} and normalized_part_number {pdata.normalized_part_number} already exists"
                )

            to_insert.append(Part(**pdata.dict()))
            created += 1
        except Exception as e:
            errors.append(str(e))
            failed += 1

    if to_insert:
        db.add_all(to_insert)
        db.commit()

    return {
        "total": len(parts_data),
        "created": created,
        "failed": failed,
        "errors": errors,
        "message": f"Created {created} parts, {failed} failed",
    }
