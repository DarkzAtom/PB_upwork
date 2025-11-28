from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from typing import List

from PB_upwork.app.shipping_zones.shipping_zones_schema import (
    ShippingZoneCreate,
    ShippingZoneUpdate,
    ShippingZoneResponse,
)
from PB_upwork.app.shipping_zones.shipping_zones_model import ShippingZone
from PB_upwork.app.shipping_rates.shipping_rates_model import ShippingRate
from PB_upwork.app.warehouses.warehouses_model import Warehouse
from db_connection import engine

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/api/shippingzones/admin", tags=["shipping-zones-admin"])


@router.get("/", response_model=List[ShippingZoneResponse])
# Admin: list shipping zones
async def list_shipping_zones_admin(
    skip: int = Query(0, ge=0, description="Pagination: skip N results"),
    limit: int = Query(50, ge=1, le=500, description="Pagination: max results (default 50, max 500)"),
    db: Session = Depends(get_db),
):
    zones = db.query(ShippingZone).offset(skip).limit(limit).all()
    return zones


@router.get("/search", response_model=List[ShippingZoneResponse])
# Admin: search shipping zones by name
async def search_shipping_zones_admin(
    name: str = Query(..., min_length=1, max_length=100, description="Zone name substring"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    zones = (
        db.query(ShippingZone)
        .filter(ShippingZone.name.ilike(f"%{name}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return zones


@router.get("/{zone_id}", response_model=ShippingZoneResponse)
# Admin: get shipping zone detail
async def get_shipping_zone_admin(
    zone_id: int = Path(..., gt=0, description="Shipping zone ID"),
    db: Session = Depends(get_db),
):
    zone = db.query(ShippingZone).filter(ShippingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Shipping zone with ID {zone_id} not found")
    return zone


@router.get("/{zone_id}/statistics", response_model=dict)
# Admin: shipping zone statistics
async def get_shipping_zone_statistics_admin(
    zone_id: int = Path(..., gt=0, description="Shipping zone ID"),
    db: Session = Depends(get_db),
):
    zone = db.query(ShippingZone).filter(ShippingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Shipping zone with ID {zone_id} not found")

    shipping_rates_count = db.query(ShippingRate).filter(ShippingRate.shipping_zone_id == zone_id).count()
    warehouses_count = db.query(Warehouse).filter(Warehouse.shipping_zone_id == zone_id).count()

    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "total_shipping_rates": shipping_rates_count,
        "total_warehouses": warehouses_count,
        "total_related_entities": shipping_rates_count + warehouses_count,
    }


@router.post("/", response_model=ShippingZoneResponse, status_code=201)
# Admin: create shipping zone
async def create_shipping_zone_admin(zone: ShippingZoneCreate, db: Session = Depends(get_db)):
    existing = db.query(ShippingZone).filter(
        ShippingZone.name == zone.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Shipping zone name '{zone.name}' already exists (ID: {existing.id})"
        )
    
    db_zone = ShippingZone(**zone.dict())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    
    return db_zone


@router.put("/{zone_id}", response_model=ShippingZoneResponse)
# Admin: update shipping zone
async def update_shipping_zone_admin(
    zone_id: int = Path(..., gt=0, description="Shipping zone ID"),
    zone_update: ShippingZoneUpdate = None,
    db: Session = Depends(get_db)
):
    db_zone = db.query(ShippingZone).filter(ShippingZone.id == zone_id).first()
    
    if not db_zone:
        raise HTTPException(
            status_code=404,
            detail=f"Shipping zone with ID {zone_id} not found"
        )
    
    if zone_update.name and zone_update.name != db_zone.name:
        existing = db.query(ShippingZone).filter(
            ShippingZone.name == zone_update.name,
            ShippingZone.id != zone_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Shipping zone name '{zone_update.name}' already exists"
            )
    
    update_data = zone_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_zone, key, value)
    
    db.commit()
    db.refresh(db_zone)
    
    return db_zone


@router.delete("/{zone_id}", status_code=204)
# Admin: delete shipping zone
async def delete_shipping_zone_admin(
    zone_id: int = Path(..., gt=0, description="Shipping zone ID"),
    force: bool = Query(False, description="Force delete even if rates/warehouses exist"),
    db: Session = Depends(get_db)
):
    db_zone = db.query(ShippingZone).filter(ShippingZone.id == zone_id).first()
    
    if not db_zone:
        raise HTTPException(
            status_code=404,
            detail=f"Shipping zone with ID {zone_id} not found"
        )
    
    rates_count = db.query(ShippingRate).filter(
        ShippingRate.shipping_zone_id == zone_id
    ).count()
    
    warehouses_count = db.query(Warehouse).filter(
        Warehouse.shipping_zone_id == zone_id
    ).count()
    
    total_refs = rates_count + warehouses_count
    
    if total_refs > 0 and not force:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete shipping zone: has {rates_count} shipping rates and {warehouses_count} warehouses. Use force=true to delete anyway."
        )
    
    db.delete(db_zone)
    db.commit()


@router.post("/bulk-create", response_model=dict, status_code=201)
# Admin: bulk create shipping zones
async def bulk_create_shipping_zones_admin(
    zones_data: List[ShippingZoneCreate],
    db: Session = Depends(get_db)
):
    created = 0
    failed = 0
    errors = []
    zones_to_insert = []

    for idx, zone_data in enumerate(zones_data):
        try:
            existing = db.query(ShippingZone).filter(
                ShippingZone.name == zone_data.name
            ).first()
            if existing:
                errors.append(f"Row {idx + 1}: Zone name '{zone_data.name}' already exists (ID: {existing.id})")
                failed += 1
                continue
            
            zones_to_insert.append(ShippingZone(**zone_data.dict()))
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    if zones_to_insert:
        db.add_all(zones_to_insert)
        db.commit()
        created = len(zones_to_insert)

    return {
        "created": created,
        "failed": failed,
        "total": len(zones_data),
        "errors": errors if errors else None
    }


@router.post("/bulk-delete", response_model=dict, status_code=200)
# Admin: bulk delete shipping zones
async def bulk_delete_shipping_zones_admin(
    zone_ids: List[int] = Query(..., description="List of shipping zone IDs to delete"),
    force: bool = Query(False, description="Force delete even if rates/warehouses exist"),
    db: Session = Depends(get_db)
):
    deleted = 0
    failed = 0
    errors = []

    for zone_id in zone_ids:
        try:
            db_zone = db.query(ShippingZone).filter(ShippingZone.id == zone_id).first()
            
            if not db_zone:
                errors.append(f"ID {zone_id}: Shipping zone not found")
                failed += 1
                continue
            
            rates_count = db.query(ShippingRate).filter(
                ShippingRate.shipping_zone_id == zone_id
            ).count()
            
            warehouses_count = db.query(Warehouse).filter(
                Warehouse.shipping_zone_id == zone_id
            ).count()
            
            total_refs = rates_count + warehouses_count
            
            if total_refs > 0 and not force:
                errors.append(f"ID {zone_id}: Has {rates_count} rates and {warehouses_count} warehouses. Set force=true to delete")
                failed += 1
                continue
            
            db.delete(db_zone)
            deleted += 1
        except Exception as e:
            errors.append(f"ID {zone_id}: {str(e)}")
            failed += 1

    db.commit()

    return {
        "deleted": deleted,
        "failed": failed,
        "total": len(zone_ids),
        "errors": errors if errors else None
    }


@router.get("/{zone_id}/warehouses", response_model=list)
# Admin: list warehouses for zone
async def get_zone_warehouses_admin(
    zone_id: int = Path(..., gt=0, description="Shipping zone ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    zone = db.query(ShippingZone).filter(ShippingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Shipping zone with ID {zone_id} not found")

    warehouses = (
        db.query(Warehouse)
        .filter(Warehouse.shipping_zone_id == zone_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": warehouse.id,
            "name": warehouse.name,
            "supplier_id": warehouse.supplier_id,
            "country": warehouse.country,
            "region": warehouse.region,
            "default_lead_time_days": warehouse.default_lead_time_days,
        }
        for warehouse in warehouses
    ]
@router.get("/statistics", response_model=dict)
# Admin: shipping zones global statistics
async def get_shipping_zones_statistics_admin(db: Session = Depends(get_db)):
    total_zones = db.query(ShippingZone).count()
    
    total_rates = db.query(ShippingRate).count()
    
    total_warehouses = db.query(Warehouse).count()
    
    zones_with_rates = db.query(ShippingZone).join(
        ShippingRate, ShippingZone.id == ShippingRate.shipping_zone_id
    ).count()
    
    zones_with_warehouses = db.query(ShippingZone).join(
        Warehouse, ShippingZone.id == Warehouse.shipping_zone_id
    ).count()
    
    zones_without_rates = total_zones - zones_with_rates
    zones_without_warehouses = total_zones - zones_with_warehouses
    
    return {
        "total_zones": total_zones,
        "total_shipping_rates_in_system": total_rates,
        "total_warehouses_in_system": total_warehouses,
        "zones_with_shipping_rates": zones_with_rates,
        "zones_without_shipping_rates": zones_without_rates,
        "zones_with_warehouses": zones_with_warehouses,
        "zones_without_warehouses": zones_without_warehouses
    }
