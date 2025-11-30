from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.warehouses.warehouses_schema import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
)
from app.warehouses.warehouses_model import Warehouse
from app.suppliers.suppliers_model import Supplier
from app.shipping_zones.shipping_zones_model import ShippingZone
from app.supplier_price.supplier_price_model import SupplierPrice
from db_routers_connection import get_db

router = APIRouter(prefix="/api/warehouses/admin", tags=["warehouses", "admin"])

# Admin: list warehouses (paginated)
@router.get("/all", response_model=List[WarehouseResponse])
async def list_warehouses_admin(
    skip: int = Query(0, ge=0, description="Pagination: skip N results"),
    limit: int = Query(50, ge=1, le=500, description="Pagination: max results (default 50, max 500)"),
    db: Session = Depends(get_db)
):
    warehouses = db.query(Warehouse).offset(skip).limit(limit).all()
    return warehouses

# Admin: search warehouses by substring match on name
@router.get("/search", response_model=List[WarehouseResponse])
async def search_warehouses(
    name: str = Query(..., min_length=1, max_length=100, description="Warehouse name to search (substring)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    warehouses = db.query(Warehouse).filter(
        Warehouse.name.ilike(f"%{name}%")
    ).offset(skip).limit(limit).all()
    
    return warehouses

# Admin: list warehouses for a given supplier
@router.get("/by-supplier/{supplier_id}", response_model=List[WarehouseResponse])
async def get_warehouses_by_supplier(
    supplier_id: int = Path(..., gt=0, description="Supplier ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier with ID {supplier_id} not found"
        )
    
    warehouses = db.query(Warehouse).filter(
        Warehouse.supplier_id == supplier_id
    ).offset(skip).limit(limit).all()
    
    return warehouses

# Admin: list warehouses belonging to a shipping zone
@router.get("/by-zone/{shipping_zone_id}", response_model=List[WarehouseResponse])
async def get_warehouses_by_shipping_zone(
    shipping_zone_id: int = Path(..., gt=0, description="Shipping zone ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    zone = db.query(ShippingZone).filter(ShippingZone.id == shipping_zone_id).first()
    
    if not zone:
        raise HTTPException(
            status_code=404,
            detail=f"Shipping zone with ID {shipping_zone_id} not found"
        )
    
    warehouses = db.query(Warehouse).filter(
        Warehouse.shipping_zone_id == shipping_zone_id
    ).offset(skip).limit(limit).all()
    
    return warehouses

# Admin: list warehouses by country (case-insensitive)
@router.get("/by-country/{country}", response_model=List[WarehouseResponse])
async def get_warehouses_by_country(
    country: str = Path(..., min_length=1, max_length=200, description="Country name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    warehouses = db.query(Warehouse).filter(
        Warehouse.country.ilike(country)
    ).offset(skip).limit(limit).all()
    
    return warehouses

# Admin: statistics
@router.get("/statistics", response_model=dict)
async def get_warehouses_statistics(
    db: Session = Depends(get_db)
):
    total_warehouses = db.query(Warehouse).count()
    
    total_suppliers = db.query(Supplier).count()
    total_zones = db.query(ShippingZone).count()
    total_inventory_entries = db.query(SupplierPrice).count()
    avg_lead_time = db.query(func.avg(Warehouse.default_lead_time_days)).scalar() or 0
    total_suppliers_with_warehouses = db.query(Warehouse.supplier_id).distinct().count()

    return {
        "total_warehouses": total_warehouses,
        "total_suppliers_with_warehouses": total_suppliers_with_warehouses,
        "total_shipping_zones": total_zones,
        "total_inventory_entries_in_system": total_inventory_entries,
        "average_lead_time_days": round(float(avg_lead_time), 2) if avg_lead_time else 0,
        "total_available_suppliers": total_suppliers
    }

# Admin: get warehouse detail
@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: int = Path(..., gt=0, description="Warehouse ID"),
    db: Session = Depends(get_db)
):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    
    if not warehouse:
        raise HTTPException(
            status_code=404,
            detail=f"Warehouse with ID {warehouse_id} not found"
        )
    
    return warehouse

# Admin: aggregate inventory count for a warehouse
@router.get("/{warehouse_id}/inventory-count", response_model=dict)
async def get_warehouse_inventory_count(
    warehouse_id: int = Path(..., gt=0, description="Warehouse ID"),
    db: Session = Depends(get_db)
):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    
    if not warehouse:
        raise HTTPException(
            status_code=404,
            detail=f"Warehouse with ID {warehouse_id} not found"
        )
    
    supplier_prices_count = db.query(SupplierPrice).filter(
        SupplierPrice.warehouse_id == warehouse_id
    ).count()
    
    return {
        "warehouse_id": warehouse.id,
        "warehouse_name": warehouse.name,
        "supplier_id": warehouse.supplier_id,
        "country": warehouse.country,
        "region": warehouse.region,
        "total_inventory_entries": supplier_prices_count,
        "default_lead_time_days": warehouse.default_lead_time_days
    }

# Admin: create
@router.post("/", response_model=WarehouseResponse, status_code=201)
async def create_warehouse(
    warehouse: WarehouseCreate,
    db: Session = Depends(get_db)
):
    supplier = db.query(Supplier).filter(Supplier.id == warehouse.supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier with ID {warehouse.supplier_id} not found"
        )
    
    zone = db.query(ShippingZone).filter(ShippingZone.id == warehouse.shipping_zone_id).first()
    
    if not zone:
        raise HTTPException(
            status_code=404,
            detail=f"Shipping zone with ID {warehouse.shipping_zone_id} not found"
        )
    
    existing = db.query(Warehouse).filter(
        Warehouse.name == warehouse.name,
        Warehouse.supplier_id == warehouse.supplier_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Warehouse name '{warehouse.name}' already exists for supplier ID {warehouse.supplier_id} (Warehouse ID: {existing.id})"
        )
    
    db_warehouse = Warehouse(**warehouse.dict())
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    
    return db_warehouse


# Admin: update
@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: int = Path(..., gt=0, description="Warehouse ID"),
    warehouse_update: WarehouseUpdate = None,
    db: Session = Depends(get_db)
):
    db_warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    
    if not db_warehouse:
        raise HTTPException(
            status_code=404,
            detail=f"Warehouse with ID {warehouse_id} not found"
        )
    
    if warehouse_update.supplier_id and warehouse_update.supplier_id != db_warehouse.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == warehouse_update.supplier_id).first()
        if not supplier:
            raise HTTPException(
                status_code=404,
                detail=f"Supplier with ID {warehouse_update.supplier_id} not found"
            )
    
    if warehouse_update.shipping_zone_id and warehouse_update.shipping_zone_id != db_warehouse.shipping_zone_id:
        zone = db.query(ShippingZone).filter(ShippingZone.id == warehouse_update.shipping_zone_id).first()
        if not zone:
            raise HTTPException(
                status_code=404,
                detail=f"Shipping zone with ID {warehouse_update.shipping_zone_id} not found"
            )
    
    if warehouse_update.name and warehouse_update.name != db_warehouse.name:
        supplier_id = warehouse_update.supplier_id or db_warehouse.supplier_id
        existing = db.query(Warehouse).filter(
            Warehouse.name == warehouse_update.name,
            Warehouse.supplier_id == supplier_id,
            Warehouse.id != warehouse_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Warehouse name '{warehouse_update.name}' already exists for this supplier"
            )
    
    update_data = warehouse_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_warehouse, key, value)
    
    db.commit()
    db.refresh(db_warehouse)
    
    return db_warehouse

# Admin: delete
@router.delete("/{warehouse_id}", status_code=204)
async def delete_warehouse(
    warehouse_id: int = Path(..., gt=0, description="Warehouse ID"),
    force: bool = Query(False, description="Force delete even if inventory exists"),
    db: Session = Depends(get_db)
):
    db_warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    
    if not db_warehouse:
        raise HTTPException(
            status_code=404,
            detail=f"Warehouse with ID {warehouse_id} not found"
        )
    
    inventory_count = db.query(SupplierPrice).filter(
        SupplierPrice.warehouse_id == warehouse_id
    ).count()
    
    if inventory_count > 0 and not force:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete warehouse: has {inventory_count} inventory entries. Use force=true to delete anyway."
        )
    
    db.delete(db_warehouse)
    db.commit()

# Admin: bulk create
@router.post("/bulk-create", response_model=dict, status_code=201)
async def bulk_create_warehouses(
    warehouses_data: List[WarehouseCreate],
    db: Session = Depends(get_db)
):
    created = 0
    failed = 0
    errors = []
    warehouses_to_insert = []

    for idx, warehouse_data in enumerate(warehouses_data):
        try:
            supplier = db.query(Supplier).filter(Supplier.id == warehouse_data.supplier_id).first()
            if not supplier:
                errors.append(f"Row {idx + 1}: Supplier with ID {warehouse_data.supplier_id} not found")
                failed += 1
                continue
            
            zone = db.query(ShippingZone).filter(ShippingZone.id == warehouse_data.shipping_zone_id).first()
            if not zone:
                errors.append(f"Row {idx + 1}: Shipping zone with ID {warehouse_data.shipping_zone_id} not found")
                failed += 1
                continue
            
            existing = db.query(Warehouse).filter(
                Warehouse.name == warehouse_data.name,
                Warehouse.supplier_id == warehouse_data.supplier_id
            ).first()
            if existing:
                errors.append(f"Row {idx + 1}: Warehouse name '{warehouse_data.name}' already exists for supplier ID {warehouse_data.supplier_id}")
                failed += 1
                continue
            
            warehouses_to_insert.append(Warehouse(**warehouse_data.dict()))
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    if warehouses_to_insert:
        db.add_all(warehouses_to_insert)
        db.commit()
        created = len(warehouses_to_insert)

    return {
        "created": created,
        "failed": failed,
        "total": len(warehouses_data),
        "errors": errors if errors else None
    }
# Admin: bulk delete
@router.post("/bulk-delete", response_model=dict, status_code=200)
async def bulk_delete_warehouses(
    warehouse_ids: List[int] = Query(..., description="List of warehouse IDs to delete"),
    force: bool = Query(False, description="Force delete even if inventory exists"),
    db: Session = Depends(get_db)
):
    deleted = 0
    failed = 0
    errors = []

    for idx, warehouse_id in enumerate(warehouse_ids):
        try:
            db_warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            
            if not db_warehouse:
                errors.append(f"ID {warehouse_id}: Warehouse not found")
                failed += 1
                continue
            
            inventory_count = db.query(SupplierPrice).filter(
                SupplierPrice.warehouse_id == warehouse_id
            ).count()
            
            if inventory_count > 0 and not force:
                errors.append(f"ID {warehouse_id}: Has {inventory_count} inventory entries. Set force=true to delete")
                failed += 1
                continue
            
            db.delete(db_warehouse)
            deleted += 1
        except Exception as e:
            errors.append(f"ID {warehouse_id}: {str(e)}")
            failed += 1

    db.commit()

    return {
        "deleted": deleted,
        "failed": failed,
        "total": len(warehouse_ids),
        "errors": errors if errors else None
    }


# Admin: filter by supplier and shipping zone
@router.get("/filter/by-supplier-and-zone", response_model=List[WarehouseResponse])
async def filter_warehouses_by_supplier_and_zone(
    supplier_id: int = Query(..., gt=0, description="Supplier ID"),
    shipping_zone_id: int = Query(..., gt=0, description="Shipping zone ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier with ID {supplier_id} not found"
        )
    
    zone = db.query(ShippingZone).filter(ShippingZone.id == shipping_zone_id).first()
    
    if not zone:
        raise HTTPException(
            status_code=404,
            detail=f"Shipping zone with ID {shipping_zone_id} not found"
        )
    
    warehouses = db.query(Warehouse).filter(
        Warehouse.supplier_id == supplier_id,
        Warehouse.shipping_zone_id == shipping_zone_id
    ).offset(skip).limit(limit).all()
    
    return warehouses
