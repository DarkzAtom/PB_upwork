from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
from typing import List

from app.pricing_rules.pricing_rules_schema import (
    PricingRuleResponse,
    PricingRuleCreate,
    PricingRuleUpdate,
)
from app.pricing_rules.pricing_rules_model import PricingRule
from app.suppliers.suppliers_model import Supplier
from app.brands.brands_model import Brand
from app.categories.categories_model import Category
from db_connection import engine

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/pricingrules/admin", tags=["pricing-rules-admin"]) 


@router.get("/", response_model=List[PricingRuleResponse])
# Admin: list pricing rules
def list_pricing_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rules = db.query(PricingRule).offset(skip).limit(limit).all()
    return rules


@router.post("/", response_model=PricingRuleResponse, status_code=201)
# Admin: create pricing rule
def create_pricing_rule(rule: PricingRuleCreate, db: Session = Depends(get_db)):
    if rule.supplier_id is not None and not db.query(Supplier).filter(Supplier.id == rule.supplier_id).first():
        raise HTTPException(status_code=404, detail="Supplier not found")
    if rule.brand_id is not None and not db.query(Brand).filter(Brand.id == rule.brand_id).first():
        raise HTTPException(status_code=404, detail="Brand not found")
    if rule.category_id is not None and not db.query(Category).filter(Category.id == rule.category_id).first():
        raise HTTPException(status_code=404, detail="Category not found")

    if rule.price_min >= rule.price_max:
        raise HTTPException(status_code=422, detail="price_min must be less than price_max")

    rule_name = getattr(rule, "rule_name", None) or getattr(rule, "name", None)
    if not rule_name:
        raise HTTPException(status_code=422, detail="rule_name (alias 'name') is required")

    if db.query(PricingRule).filter(PricingRule.rule_name == rule_name).first():
        raise HTTPException(status_code=422, detail="Pricing rule name already exists")

    new_rule = PricingRule(
        rule_name=rule_name,
        supplier_id=rule.supplier_id,
        brand_id=rule.brand_id,
        category_id=rule.category_id,
        price_min=rule.price_min,
        price_max=rule.price_max,
        warehouse_region=rule.warehouse_region,
        margin_percent=rule.margin_percent,
        fixed_markup=rule.fixed_markup,
        rounding_rule=rule.rounding_rule,
        priority=rule.priority,
        is_active=rule.is_active,
    )

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule


@router.put("/{rule_id}", response_model=PricingRuleResponse)
# Admin: update pricing rule
def update_pricing_rule(
    rule_id: int = Path(..., gt=0),
    update_data: PricingRuleUpdate = None,
    db: Session = Depends(get_db),
):
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Pricing rule not found")

    new_name = update_data.rule_name if update_data.rule_name is not None else getattr(update_data, "name", None)
    if new_name is not None:
        if db.query(PricingRule).filter(PricingRule.rule_name == new_name, PricingRule.id != rule_id).first():
            raise HTTPException(status_code=422, detail="Pricing rule name already exists")
        rule.rule_name = new_name

    if update_data.supplier_id is not None:
        if not db.query(Supplier).filter(Supplier.id == update_data.supplier_id).first():
            raise HTTPException(status_code=404, detail="Supplier not found")
        rule.supplier_id = update_data.supplier_id

    if update_data.brand_id is not None:
        if not db.query(Brand).filter(Brand.id == update_data.brand_id).first():
            raise HTTPException(status_code=404, detail="Brand not found")
        rule.brand_id = update_data.brand_id

    if update_data.category_id is not None:
        if not db.query(Category).filter(Category.id == update_data.category_id).first():
            raise HTTPException(status_code=404, detail="Category not found")
        rule.category_id = update_data.category_id

    if update_data.price_min is not None:
        rule.price_min = update_data.price_min
    if update_data.price_max is not None:
        rule.price_max = update_data.price_max
    if rule.price_min >= rule.price_max:
        raise HTTPException(status_code=422, detail="price_min must be less than price_max")

    if update_data.warehouse_region is not None:
        rule.warehouse_region = update_data.warehouse_region
    if update_data.margin_percent is not None:
        rule.margin_percent = update_data.margin_percent
    if update_data.fixed_markup is not None:
        rule.fixed_markup = update_data.fixed_markup
    if update_data.rounding_rule is not None:
        rule.rounding_rule = update_data.rounding_rule
    if update_data.priority is not None:
        rule.priority = update_data.priority
    if update_data.is_active is not None:
        rule.is_active = update_data.is_active

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
# Admin: delete pricing rule
def delete_pricing_rule(rule_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Pricing rule not found")
    db.delete(rule)
    db.commit()


@router.post("/bulk-create", response_model=dict, status_code=201)
# Admin: bulk create pricing rules
def bulk_create_pricing_rules(
    rules_data: List[PricingRuleCreate], db: Session = Depends(get_db)
):
    if not rules_data:
        raise HTTPException(status_code=422, detail="Empty rules list")

    created = 0
    failed = 0
    errors: List[str] = []
    to_insert: List[PricingRule] = []

    for idx, rd in enumerate(rules_data, 1):
        try:
            if rd.supplier_id is not None and not db.query(Supplier).filter(Supplier.id == rd.supplier_id).first():
                raise ValueError("Supplier not found")
            if rd.brand_id is not None and not db.query(Brand).filter(Brand.id == rd.brand_id).first():
                raise ValueError("Brand not found")
            if rd.category_id is not None and not db.query(Category).filter(Category.id == rd.category_id).first():
                raise ValueError("Category not found")

            if rd.price_min >= rd.price_max:
                raise ValueError("price_min must be less than price_max")

            rd_name = getattr(rd, "rule_name", None) or getattr(rd, "name", None)
            if not rd_name:
                raise ValueError("rule_name (alias 'name') is required")

            if db.query(PricingRule).filter(PricingRule.rule_name == rd_name).first():
                raise ValueError("rule_name already exists")

            to_insert.append(
                PricingRule(
                    rule_name=rd_name,
                    supplier_id=rd.supplier_id,
                    brand_id=rd.brand_id,
                    category_id=rd.category_id,
                    price_min=rd.price_min,
                    price_max=rd.price_max,
                    warehouse_region=rd.warehouse_region,
                    margin_percent=rd.margin_percent,
                    fixed_markup=rd.fixed_markup,
                    rounding_rule=rd.rounding_rule,
                    priority=rd.priority,
                    is_active=rd.is_active,
                )
            )
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
            failed += 1

    if to_insert:
        db.add_all(to_insert)
        db.commit()
        created = len(to_insert)

    return {"created": created, "failed": failed, "total": len(rules_data), "errors": errors or None}


@router.post("/bulk-delete", response_model=dict)
# Admin: bulk delete pricing rules
def bulk_delete_pricing_rules(
    rule_ids: List[int] = Query(..., description="IDs to delete"),
    db: Session = Depends(get_db),
):
    if not rule_ids:
        raise HTTPException(status_code=422, detail="Empty rule_ids list")

    deleted = 0
    failed = 0
    errors: List[str] = []

    for rid in rule_ids:
        rule = db.query(PricingRule).filter(PricingRule.id == rid).first()
        if not rule:
            errors.append(f"ID {rid}: not found")
            failed += 1
            continue
        db.delete(rule)
        deleted += 1

    db.commit()
    return {"deleted": deleted, "failed": failed, "total": len(rule_ids), "errors": errors or None}


@router.get("/statistics", response_model=dict)
# Admin: pricing rules statistics
def get_pricing_rules_statistics(db: Session = Depends(get_db)):
    total_rules = db.query(PricingRule).count()
    active_rules = db.query(PricingRule).filter(PricingRule.is_active == True).count()
    inactive_rules = db.query(PricingRule).filter(PricingRule.is_active == False).count()

    unique_suppliers = db.query(PricingRule.supplier_id).distinct().count()
    unique_brands = db.query(PricingRule.brand_id).distinct().count()
    unique_categories = db.query(PricingRule.category_id).distinct().count()
    unique_regions = db.query(PricingRule.warehouse_region).distinct().count()

    avg_margin = db.query(func.avg(PricingRule.margin_percent)).scalar() or 0
    min_margin = db.query(func.min(PricingRule.margin_percent)).scalar() or 0
    max_margin = db.query(func.max(PricingRule.margin_percent)).scalar() or 0
    avg_fixed_markup = db.query(func.avg(PricingRule.fixed_markup)).scalar() or 0
    min_price = db.query(func.min(PricingRule.price_min)).scalar() or 0
    max_price = db.query(func.max(PricingRule.price_max)).scalar() or 0
    highest_priority = db.query(func.max(PricingRule.priority)).scalar() or 0

    return {
        "total_pricing_rules": total_rules,
        "active_rules": active_rules,
        "inactive_rules": inactive_rules,
        "unique_suppliers": unique_suppliers,
        "unique_brands": unique_brands,
        "unique_categories": unique_categories,
        "unique_regions": unique_regions,
        "average_margin_percent": float(avg_margin),
        "min_margin_percent": float(min_margin),
        "max_margin_percent": float(max_margin),
        "average_fixed_markup": float(avg_fixed_markup),
        "min_price_range": float(min_price),
        "max_price_range": float(max_price),
        "highest_priority_level": highest_priority,
    }


@router.get("/by-active/{is_active}", response_model=List[PricingRuleResponse])
# Admin: list pricing rules by active status
def get_rules_by_active_status(
    is_active: bool, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)
):
    rules = (
        db.query(PricingRule)
        .filter(PricingRule.is_active == is_active)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rules


@router.get("/by-supplier/{supplier_id}", response_model=List[PricingRuleResponse])
# Admin: list pricing rules by supplier
def get_rules_by_supplier(
    supplier_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rules = (
        db.query(PricingRule)
        .filter(PricingRule.supplier_id == supplier_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rules


@router.get("/by-brand/{brand_id}", response_model=List[PricingRuleResponse])
# Admin: list pricing rules by brand
def get_rules_by_brand(
    brand_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rules = (
        db.query(PricingRule)
        .filter(PricingRule.brand_id == brand_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rules


@router.get("/by-category/{category_id}", response_model=List[PricingRuleResponse])
# Admin: list pricing rules by category
def get_rules_by_category(
    category_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rules = (
        db.query(PricingRule)
        .filter(PricingRule.category_id == category_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rules


@router.get("/by-region/{region}", response_model=List[PricingRuleResponse])
# Admin: list pricing rules by region
def get_rules_by_region(
    region: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rules = (
        db.query(PricingRule)
        .filter(PricingRule.warehouse_region.ilike(f"%{region}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rules


@router.get("/by-priority/{priority}", response_model=List[PricingRuleResponse])
# Admin: list pricing rules by priority
def get_rules_by_priority(
    priority: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rules = (
        db.query(PricingRule)
        .filter(PricingRule.priority == priority)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rules


@router.get("/search", response_model=List[PricingRuleResponse])
# Admin: search pricing rules by name
def search_pricing_rules(
    name: str = Query(..., min_length=1, max_length=200),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rules = (
        db.query(PricingRule)
        .filter(PricingRule.rule_name.ilike(f"%{name}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rules


@router.get("/price-range-analysis", response_model=dict)
# Admin: analyze pricing rule price ranges
def get_price_range_analysis(db: Session = Depends(get_db)):
    total_rules = db.query(PricingRule).count()
    rules = db.query(PricingRule).all()

    price_ranges: dict[str, int] = {}
    for r in rules:
        key = f"{float(r.price_min)}-{float(r.price_max)}"
        price_ranges[key] = price_ranges.get(key, 0) + 1

    avg_price_range = (
        sum((float(r.price_max) - float(r.price_min)) for r in rules) / total_rules
        if total_rules > 0
        else 0
    )

    return {
        "total_rules": total_rules,
        "average_price_range_width": avg_price_range,
        "price_range_distribution": price_ranges,
        "min_price_overall": float(min(r.price_min for r in rules)) if rules else 0,
        "max_price_overall": float(max(r.price_max for r in rules)) if rules else 0,
    }


@router.get("/{rule_id}", response_model=PricingRuleResponse)
# Admin: get pricing rule detail
def get_pricing_rule(
    rule_id: int = Path(..., gt=0), db: Session = Depends(get_db)
):
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Pricing rule not found")
    return rule
