from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from typing import List

from app.suppliers.suppliers_schema import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from app.suppliers.suppliers_model import Supplier
from app.warehouses.warehouses_model import Warehouse
from app.supplier_price.supplier_price_model import SupplierPrice
from app.parts.parts_model import Part
from app.pricing_rules.pricing_rules_model import PricingRule
from db_connection import engine

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/suppliers/admin", tags=["suppliers-admin"])


@router.get("/search", response_model=List[SupplierResponse])
# Admin: search suppliers by name
async def search_suppliers(
    name: str = Query(..., min_length=1, max_length=200),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    suppliers = (
        db.query(Supplier)
        .filter(Supplier.name.ilike(f"%{name}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return suppliers


@router.get("/all", response_model=List[SupplierResponse])
# Admin: list all suppliers
async def list_all_suppliers_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    suppliers = db.query(Supplier).offset(skip).limit(limit).all()
    return suppliers


@router.get("/statistics", response_model=dict)
# Admin: supplier statistics
async def supplier_statistics(db: Session = Depends(get_db)):
    total_suppliers = db.query(Supplier).count()

    suppliers_with_warehouses = (
        db.query(Supplier)
        .join(Warehouse, Warehouse.supplier_id == Supplier.id)
        .distinct()
        .count()
    )
    # Parts table doesn't have supplier_id column
    suppliers_with_parts = 0
    suppliers_with_prices = (
        db.query(Supplier)
        .join(SupplierPrice, SupplierPrice.supplier_id == Supplier.id)
        .distinct()
        .count()
    )
    suppliers_with_rules = (
        db.query(Supplier)
        .join(PricingRule, PricingRule.supplier_id == Supplier.id)
        .distinct()
        .count()
    )

    return {
        "total_suppliers": total_suppliers,
        "suppliers_with_warehouses": suppliers_with_warehouses,
        "suppliers_with_parts": suppliers_with_parts,
        "suppliers_with_prices": suppliers_with_prices,
        "suppliers_with_pricing_rules": suppliers_with_rules,
    }


@router.post("/bulk-create", response_model=dict, status_code=201)
# Admin: bulk create suppliers
async def bulk_create_suppliers(suppliers_data: List[SupplierCreate], db: Session = Depends(get_db)):
    created = 0
    failed = 0
    errors = []
    to_insert: List[Supplier] = []

    for idx, s in enumerate(suppliers_data):
        try:
            existing = db.query(Supplier).filter(Supplier.name == s.name).first()
            if existing:
                errors.append(
                    f"Row {idx + 1}: Supplier name '{s.name}' already exists (ID: {existing.id})"
                )
                failed += 1
                continue
            to_insert.append(Supplier(**s.dict()))
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    if to_insert:
        db.add_all(to_insert)
        db.commit()
        created = len(to_insert)

    return {
        "total": len(suppliers_data),
        "created": created,
        "failed": failed,
        "errors": errors or None,
    }


@router.post("/bulk-delete", response_model=dict)
# Admin: bulk delete suppliers
async def bulk_delete_suppliers(
    supplier_ids: List[int] = Query(..., description="Supplier IDs to delete"),
    force: bool = Query(False),
    db: Session = Depends(get_db),
):
    deleted = 0
    failed = 0
    errors = []

    for sid in supplier_ids:
        try:
            s = db.query(Supplier).filter(Supplier.id == sid).first()
            if not s:
                errors.append(f"ID {sid}: Supplier not found")
                failed += 1
                continue

            if not force:
                deps_total = (
                    db.query(Warehouse).filter(Warehouse.supplier_id == sid).count()
                    + db.query(SupplierPrice).filter(SupplierPrice.supplier_id == sid).count()
                    + db.query(PricingRule).filter(PricingRule.supplier_id == sid).count()
                )
                if deps_total > 0:
                    errors.append(
                        f"ID {sid}: Has dependent records ({deps_total}). Set force=true to delete."
                    )
                    failed += 1
                    continue

            db.delete(s)
            deleted += 1
        except Exception as e:
            errors.append(f"ID {sid}: {str(e)}")
            failed += 1

    db.commit()

    return {
        "total": len(supplier_ids),
        "deleted": deleted,
        "failed": failed,
        "errors": errors or None,
    }


@router.get("/{supplier_id}/warehouses", response_model=list)
# Admin: list supplier warehouses
async def get_supplier_warehouses(
    supplier_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    warehouses = (
        db.query(Warehouse)
        .filter(Warehouse.supplier_id == supplier_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": w.id,
            "supplier_id": w.supplier_id,
            "name": w.name,
            "country": w.country,
            "region": w.region,
            "shipping_zone_id": w.shipping_zone_id,
            "default_lead_time_days": w.default_lead_time_days,
        }
        for w in warehouses
    ]


@router.get("/{supplier_id}/parts-count", response_model=dict)
# Admin: count parts supplied by supplier
async def get_supplier_parts_count(
    supplier_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Parts table doesn't have supplier_id column, so always return 0
    count = 0
    return {"supplier_id": supplier_id, "parts_count": count}


@router.post("/", response_model=SupplierResponse, status_code=201)
# Admin: create supplier
async def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    existing = db.query(Supplier).filter(Supplier.name == supplier.name).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Supplier name '{supplier.name}' already exists (ID: {existing.id})",
        )

    db_supplier = Supplier(**supplier.dict())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


@router.get("/{supplier_id}", response_model=SupplierResponse)
# Admin: get supplier detail
async def get_supplier_admin(
    supplier_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
# Admin: update supplier
async def update_supplier(
    supplier_id: int = Path(..., gt=0),
    supplier_update: SupplierUpdate = None,
    db: Session = Depends(get_db),
):
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    if supplier_update and supplier_update.name and supplier_update.name != db_supplier.name:
        existing = db.query(Supplier).filter(Supplier.name == supplier_update.name).first()
        if existing and existing.id != supplier_id:
            raise HTTPException(status_code=409, detail="Supplier name already exists")

    update_data = (supplier_update.dict(exclude_unset=True) if supplier_update else {})
    for key, value in update_data.items():
        setattr(db_supplier, key, value)

    db.commit()
    db.refresh(db_supplier)
    return db_supplier


@router.delete("/{supplier_id}", status_code=204)
# Admin: delete supplier
async def delete_supplier(
    supplier_id: int = Path(..., gt=0),
    force: bool = Query(False, description="Force delete even if dependencies exist"),
    db: Session = Depends(get_db),
):
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    deps = {
        "warehouses": db.query(Warehouse).filter(Warehouse.supplier_id == supplier_id).count(),
        "supplier_prices": db.query(SupplierPrice).filter(SupplierPrice.supplier_id == supplier_id).count(),
        "pricing_rules": db.query(PricingRule).filter(PricingRule.supplier_id == supplier_id).count(),
    }

    if not force and any(v > 0 for v in deps.values()):
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot delete supplier with existing references. "
                f"Dependencies: {deps}. Set force=true to delete anyway."
            ),
        )

    db.delete(db_supplier)
    db.commit()
