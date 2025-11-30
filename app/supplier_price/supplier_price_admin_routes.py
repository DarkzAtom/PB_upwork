from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
from typing import List

from app.supplier_price.supplier_price_schema import (
    SupplierPriceCreate,
    SupplierPriceUpdate,
    SupplierPriceResponse,
)
from app.supplier_price.supplier_price_model import SupplierPrice
from app.parts.parts_model import Part
from app.suppliers.suppliers_model import Supplier
from app.warehouses.warehouses_model import Warehouse
from db_connection import engine

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/supplierprice/admin", tags=["supplierprice-admin"])


@router.get("/all", response_model=List[SupplierPriceResponse])
# Admin: list supplier prices
async def list_all_supplier_prices_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    prices = db.query(SupplierPrice).offset(skip).limit(limit).all()
    return prices


@router.post("/", response_model=SupplierPriceResponse, status_code=201)
# Admin: create supplier price
async def create_supplier_price(
    price: SupplierPriceCreate,
    db: Session = Depends(get_db)
):
    part = db.query(Part).filter(Part.id == price.part_id).first()
    
    if not part:
        raise HTTPException(
            status_code=404,
            detail=f"Part with ID {price.part_id} not found"
        )
    
    supplier = db.query(Supplier).filter(Supplier.id == price.supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier with ID {price.supplier_id} not found"
        )
    
    warehouse = db.query(Warehouse).filter(Warehouse.id == price.warehouse_id).first()
    
    if not warehouse:
        raise HTTPException(
            status_code=404,
            detail=f"Warehouse with ID {price.warehouse_id} not found"
        )
    
    db_price = SupplierPrice(**price.dict())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    
    return db_price


@router.get("/statistics", response_model=dict)
# Admin: supplier prices statistics
async def get_supplier_prices_statistics(
    db: Session = Depends(get_db)
):
    total_prices = db.query(SupplierPrice).count()
    
    total_parts = db.query(Part).count()
    
    total_suppliers = db.query(Supplier).count()
    
    total_warehouses = db.query(Warehouse).count()
    
    parts_with_prices = db.query(Part).join(
        SupplierPrice, Part.id == SupplierPrice.part_id
    ).count()
    
    suppliers_with_prices = db.query(Supplier).join(
        SupplierPrice, Supplier.id == SupplierPrice.supplier_id
    ).count()
    
    warehouses_with_prices = db.query(Warehouse).join(
        SupplierPrice, Warehouse.id == SupplierPrice.warehouse_id
    ).count()
    
    avg_price = db.query(SupplierPrice).with_entities(
        func.avg(SupplierPrice.base_price).label('avg_price')
    ).scalar() or 0
    
    min_price = db.query(SupplierPrice).with_entities(
        func.min(SupplierPrice.base_price).label('min_price')
    ).scalar() or 0
    
    max_price = db.query(SupplierPrice).with_entities(
        func.max(SupplierPrice.base_price).label('max_price')
    ).scalar() or 0
    
    total_inventory = db.query(SupplierPrice).with_entities(
        func.sum(SupplierPrice.available_qty).label('total_qty')
    ).scalar() or 0
    
    return {
        "total_supplier_prices": total_prices,
        "total_parts": total_parts,
        "total_suppliers": total_suppliers,
        "total_warehouses": total_warehouses,
        "parts_with_prices": parts_with_prices,
        "suppliers_with_prices": suppliers_with_prices,
        "warehouses_with_prices": warehouses_with_prices,
        "average_price": round(float(avg_price), 4) if avg_price else 0,
        "min_price": float(min_price) if min_price else 0,
        "max_price": float(max_price) if max_price else 0,
        "total_available_inventory": int(total_inventory) if total_inventory else 0
    }


@router.get("/low-stock", response_model=List[SupplierPriceResponse])
# Admin: list low stock supplier prices
async def get_low_stock_prices(
    threshold: int = Query(10, ge=0, description="Quantity threshold (default: 10)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    prices = db.query(SupplierPrice).filter(
        SupplierPrice.available_qty <= threshold
    ).offset(skip).limit(limit).all()
    
    return prices


@router.get("/upcoming-lead-time", response_model=dict)
# Admin: lead time analysis for supplier prices
async def get_lead_time_analysis(
    db: Session = Depends(get_db)
):
    prices = db.query(SupplierPrice).all()
    
    if not prices:
        return {
            "total_prices": 0,
            "average_lead_time": 0,
            "min_lead_time": 0,
            "max_lead_time": 0,
            "zero_lead_time": 0
        }
    
    lead_times = [p.lead_time_days for p in prices]
    
    return {
        "total_prices": len(prices),
        "average_lead_time": round(sum(lead_times) / len(lead_times), 2),
        "min_lead_time": min(lead_times),
        "max_lead_time": max(lead_times),
        "zero_lead_time": len([lt for lt in lead_times if lt == 0])
    }


@router.get("/find-best-price", response_model=SupplierPriceResponse)
# Admin: find best (lowest) supplier price for part
async def admin_find_best_price(
    part_id: int = Query(..., gt=0, description="Part ID"),
    db: Session = Depends(get_db)
):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail=f"Part with ID {part_id} not found")
    best_price = (
        db.query(SupplierPrice)
        .filter(SupplierPrice.part_id == part_id)
        .order_by(SupplierPrice.base_price)
        .first()
    )
    if not best_price:
        raise HTTPException(status_code=404, detail=f"No supplier prices found for part ID {part_id}")
    return best_price


@router.get("/{price_id}", response_model=SupplierPriceResponse)
# Admin: get supplier price detail
async def get_supplier_price_admin(
    price_id: int = Path(..., gt=0, description="Supplier price ID"),
    db: Session = Depends(get_db)
):
    price = db.query(SupplierPrice).filter(SupplierPrice.id == price_id).first()
    
    if not price:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier price with ID {price_id} not found"
        )
    
    return price


@router.put("/{price_id}", response_model=SupplierPriceResponse)
# Admin: update supplier price
async def update_supplier_price(
    price_id: int = Path(..., gt=0, description="Supplier price ID"),
    price_update: SupplierPriceUpdate = None,
    db: Session = Depends(get_db)
):
    db_price = db.query(SupplierPrice).filter(SupplierPrice.id == price_id).first()
    
    if not db_price:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier price with ID {price_id} not found"
        )
    
    if price_update.part_id and price_update.part_id != db_price.part_id:
        part = db.query(Part).filter(Part.id == price_update.part_id).first()
        if not part:
            raise HTTPException(
                status_code=404,
                detail=f"Part with ID {price_update.part_id} not found"
            )
    
    if price_update.supplier_id and price_update.supplier_id != db_price.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == price_update.supplier_id).first()
        if not supplier:
            raise HTTPException(
                status_code=404,
                detail=f"Supplier with ID {price_update.supplier_id} not found"
            )
    
    if price_update.warehouse_id and price_update.warehouse_id != db_price.warehouse_id:
        warehouse = db.query(Warehouse).filter(Warehouse.id == price_update.warehouse_id).first()
        if not warehouse:
            raise HTTPException(
                status_code=404,
                detail=f"Warehouse with ID {price_update.warehouse_id} not found"
            )
    
    update_data = price_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_price, key, value)
    
    db.commit()
    db.refresh(db_price)
    
    return db_price


@router.delete("/{price_id}", status_code=204)
# Admin: delete supplier price
async def delete_supplier_price(
    price_id: int = Path(..., gt=0, description="Supplier price ID"),
    db: Session = Depends(get_db)
):
    db_price = db.query(SupplierPrice).filter(SupplierPrice.id == price_id).first()
    
    if not db_price:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier price with ID {price_id} not found"
        )
    
    db.delete(db_price)
    db.commit()


@router.post("/bulk-create", response_model=dict, status_code=201)
# Admin: bulk create supplier prices
async def bulk_create_supplier_prices(
    prices_data: List[SupplierPriceCreate],
    db: Session = Depends(get_db)
):
    created = 0
    failed = 0
    errors = []
    prices_to_insert = []

    for idx, price_data in enumerate(prices_data):
        try:
            part = db.query(Part).filter(Part.id == price_data.part_id).first()
            if not part:
                errors.append(f"Row {idx + 1}: Part with ID {price_data.part_id} not found")
                failed += 1
                continue
            
            supplier = db.query(Supplier).filter(Supplier.id == price_data.supplier_id).first()
            if not supplier:
                errors.append(f"Row {idx + 1}: Supplier with ID {price_data.supplier_id} not found")
                failed += 1
                continue
            
            warehouse = db.query(Warehouse).filter(Warehouse.id == price_data.warehouse_id).first()
            if not warehouse:
                errors.append(f"Row {idx + 1}: Warehouse with ID {price_data.warehouse_id} not found")
                failed += 1
                continue
            
            prices_to_insert.append(SupplierPrice(**price_data.dict()))
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    if prices_to_insert:
        db.add_all(prices_to_insert)
        db.commit()
        created = len(prices_to_insert)

    return {
        "created": created,
        "failed": failed,
        "total": len(prices_data),
        "errors": errors if errors else None
    }


@router.post("/bulk-delete", response_model=dict, status_code=200)
# Admin: bulk delete supplier prices
async def bulk_delete_supplier_prices(
    price_ids: List[int] = Query(..., description="List of supplier price IDs to delete"),
    db: Session = Depends(get_db)
):
    deleted = 0
    failed = 0
    errors = []

    for price_id in price_ids:
        try:
            db_price = db.query(SupplierPrice).filter(SupplierPrice.id == price_id).first()
            
            if not db_price:
                errors.append(f"ID {price_id}: Supplier price not found")
                failed += 1
                continue
            
            db.delete(db_price)
            deleted += 1
        except Exception as e:
            errors.append(f"ID {price_id}: {str(e)}")
            failed += 1

    db.commit()

    return {
        "deleted": deleted,
        "failed": failed,
        "total": len(price_ids),
        "errors": errors if errors else None
    }


@router.get("/by-stock-status/{status}", response_model=List[SupplierPriceResponse])
# Admin: list supplier prices by stock status
async def get_prices_by_stock_status(
    status: str = Path(..., min_length=1, max_length=100, description="Stock status (e.g., 'In Stock', 'Low Stock', 'Out of Stock')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    prices = db.query(SupplierPrice).filter(
        SupplierPrice.stock_status.ilike(status)
    ).offset(skip).limit(limit).all()
    
    return prices


@router.get("/by-part/{part_id}", response_model=List[SupplierPriceResponse])
# Admin: list supplier prices by part
async def admin_get_prices_by_part(
    part_id: int = Path(..., gt=0, description="Part ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail=f"Part with ID {part_id} not found")
    prices = (
        db.query(SupplierPrice)
        .filter(SupplierPrice.part_id == part_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return prices


@router.get("/by-supplier/{supplier_id}", response_model=List[SupplierPriceResponse])
# Admin: list supplier prices by supplier
async def admin_get_prices_by_supplier(
    supplier_id: int = Path(..., gt=0, description="Supplier ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier with ID {supplier_id} not found")
    prices = (
        db.query(SupplierPrice)
        .filter(SupplierPrice.supplier_id == supplier_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return prices


@router.get("/by-warehouse/{warehouse_id}", response_model=List[SupplierPriceResponse])
# Admin: list supplier prices by warehouse
async def admin_get_prices_by_warehouse(
    warehouse_id: int = Path(..., gt=0, description="Warehouse ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail=f"Warehouse with ID {warehouse_id} not found")
    prices = (
        db.query(SupplierPrice)
        .filter(SupplierPrice.warehouse_id == warehouse_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return prices


@router.get("/filter/by-part-and-supplier", response_model=List[SupplierPriceResponse])
# Admin: filter supplier prices by part and supplier
async def admin_filter_by_part_and_supplier(
    part_id: int = Query(..., gt=0, description="Part ID"),
    supplier_id: int = Query(..., gt=0, description="Supplier ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail=f"Part with ID {part_id} not found")
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier with ID {supplier_id} not found")
    prices = (
        db.query(SupplierPrice)
        .filter(
            SupplierPrice.part_id == part_id,
            SupplierPrice.supplier_id == supplier_id,
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return prices
