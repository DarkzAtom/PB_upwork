from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
from typing import List, Optional

from PB_upwork.app.shipping_rates.shipping_rates_schema import (
    ShippingRateCreate,
    ShippingRateUpdate,
    ShippingRateResponse,
)
from PB_upwork.app.shipping_rates.shipping_rates_model import ShippingRate
from PB_upwork.app.shipping_zones.shipping_zones_model import ShippingZone
from db_connection import engine

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/shippingrates/admin", tags=["shipping-rates-admin"]) 


@router.get("/", response_model=List[ShippingRateResponse])
# Admin: list shipping rates
async def list_shipping_rates_admin(
    skip: int = Query(0, ge=0, description="Pagination: skip N results"),
    limit: int = Query(50, ge=1, le=500, description="Pagination: max results (default 50, max 500)"),
    db: Session = Depends(get_db),
):
    rates = db.query(ShippingRate).offset(skip).limit(limit).all()
    return rates


@router.get("/{rate_id}", response_model=ShippingRateResponse)
# Admin: get shipping rate detail
async def get_shipping_rate_admin(
    rate_id: int = Path(..., gt=0, description="Shipping rate ID"),
    db: Session = Depends(get_db),
):
    rate = db.query(ShippingRate).filter(ShippingRate.id == rate_id).first()
    if not rate:
        raise HTTPException(status_code=404, detail=f"Shipping rate with ID {rate_id} not found")
    return rate


@router.post("/", response_model=ShippingRateResponse, status_code=201)
# Admin: create shipping rate
async def create_shipping_rate_admin(
    rate: ShippingRateCreate, db: Session = Depends(get_db)
):
    zone = db.query(ShippingZone).filter(ShippingZone.id == rate.shipping_zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Shipping zone with ID {rate.shipping_zone_id} not found")

    if rate.weight_min >= rate.weight_max:
        raise HTTPException(status_code=422, detail="weight_min must be less than weight_max")

    db_rate = ShippingRate(**rate.dict())
    db.add(db_rate)
    db.commit()
    db.refresh(db_rate)
    return db_rate


@router.put("/{rate_id}", response_model=ShippingRateResponse)
# Admin: update shipping rate
async def update_shipping_rate_admin(
    rate_id: int = Path(..., gt=0, description="Shipping rate ID"),
    rate_update: ShippingRateUpdate = None,
    db: Session = Depends(get_db),
):
    db_rate = db.query(ShippingRate).filter(ShippingRate.id == rate_id).first()
    if not db_rate:
        raise HTTPException(status_code=404, detail=f"Shipping rate with ID {rate_id} not found")

    if rate_update.shipping_zone_id and rate_update.shipping_zone_id != db_rate.shipping_zone_id:
        zone = db.query(ShippingZone).filter(ShippingZone.id == rate_update.shipping_zone_id).first()
        if not zone:
            raise HTTPException(status_code=404, detail=f"Shipping zone with ID {rate_update.shipping_zone_id} not found")

    weight_min = rate_update.weight_min if rate_update.weight_min is not None else db_rate.weight_min
    weight_max = rate_update.weight_max if rate_update.weight_max is not None else db_rate.weight_max
    if weight_min >= weight_max:
        raise HTTPException(status_code=422, detail="weight_min must be less than weight_max")

    update_data = rate_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rate, key, value)

    db.commit()
    db.refresh(db_rate)
    return db_rate


@router.delete("/{rate_id}", status_code=204)
# Admin: delete shipping rate
async def delete_shipping_rate_admin(
    rate_id: int = Path(..., gt=0, description="Shipping rate ID"),
    db: Session = Depends(get_db),
):
    db_rate = db.query(ShippingRate).filter(ShippingRate.id == rate_id).first()
    if not db_rate:
        raise HTTPException(status_code=404, detail=f"Shipping rate with ID {rate_id} not found")
    db.delete(db_rate)
    db.commit()


@router.post("/bulk-create", response_model=dict, status_code=201)
# Admin: bulk create shipping rates
async def bulk_create_shipping_rates_admin(
    rates_data: List[ShippingRateCreate], db: Session = Depends(get_db)
):
    created = 0
    failed = 0
    errors: List[str] = []
    rates_to_insert: List[ShippingRate] = []

    for idx, rate_data in enumerate(rates_data, 1):
        try:
            zone = db.query(ShippingZone).filter(ShippingZone.id == rate_data.shipping_zone_id).first()
            if not zone:
                errors.append(f"Row {idx}: Shipping zone with ID {rate_data.shipping_zone_id} not found")
                failed += 1
                continue

            if rate_data.weight_min >= rate_data.weight_max:
                errors.append(
                    f"Row {idx}: weight_min ({rate_data.weight_min}) must be less than weight_max ({rate_data.weight_max})"
                )
                failed += 1
                continue

            rates_to_insert.append(ShippingRate(**rate_data.dict()))
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
            failed += 1

    if rates_to_insert:
        db.add_all(rates_to_insert)
        db.commit()
        created = len(rates_to_insert)

    return {"created": created, "failed": failed, "total": len(rates_data), "errors": errors or None}


@router.post("/bulk-delete", response_model=dict)
# Admin: bulk delete shipping rates
async def bulk_delete_shipping_rates_admin(
    rate_ids: List[int] = Query(..., description="List of shipping rate IDs to delete"),
    db: Session = Depends(get_db),
):
    deleted = 0
    failed = 0
    errors: List[str] = []

    for rate_id in rate_ids:
        try:
            db_rate = db.query(ShippingRate).filter(ShippingRate.id == rate_id).first()
            if not db_rate:
                errors.append(f"ID {rate_id}: Shipping rate not found")
                failed += 1
                continue
            db.delete(db_rate)
            deleted += 1
        except Exception as e:
            errors.append(f"ID {rate_id}: {str(e)}")
            failed += 1

    db.commit()
    return {"deleted": deleted, "failed": failed, "total": len(rate_ids), "errors": errors or None}


@router.get("/statistics", response_model=dict)
# Admin: shipping rates statistics
async def get_shipping_rates_statistics_admin(db: Session = Depends(get_db)):
    total_rates = db.query(ShippingRate).count()
    total_zones = db.query(ShippingZone).count()
    zones_with_rates = (
        db.query(ShippingZone)
        .join(ShippingRate, ShippingZone.id == ShippingRate.shipping_zone_id)
        .count()
    )

    avg_price = db.query(func.avg(ShippingRate.price_pln)).scalar() or 0
    min_price = db.query(func.min(ShippingRate.price_pln)).scalar() or 0
    max_price = db.query(func.max(ShippingRate.price_pln)).scalar() or 0

    unique_carriers = db.query(func.count(func.distinct(ShippingRate.carrier))).scalar() or 0
    unique_regions = db.query(func.count(func.distinct(ShippingRate.warehouse_region))).scalar() or 0

    return {
        "total_shipping_rates": total_rates,
        "total_shipping_zones": total_zones,
        "zones_with_rates": zones_with_rates,
        "unique_carriers": unique_carriers,
        "unique_warehouse_regions": unique_regions,
        "average_price_pln": round(float(avg_price), 4) if avg_price else 0,
        "min_price_pln": float(min_price) if min_price else 0,
        "max_price_pln": float(max_price) if max_price else 0,
    }


@router.get("/by-carrier/{carrier}", response_model=dict)
# Admin: carrier shipping rates statistics
async def get_carrier_statistics_admin(
    carrier: str = Path(..., min_length=1, max_length=200, description="Carrier name"),
    db: Session = Depends(get_db),
):
    rates = db.query(ShippingRate).filter(ShippingRate.carrier.ilike(f"%{carrier}%")).all()
    if not rates:
        raise HTTPException(status_code=404, detail=f"No rates found for carrier '{carrier}'")

    prices = [float(getattr(r, "price_pln", 0) or 0) for r in rates]

    return {
        "carrier": carrier,
        "total_rates": len(rates),
        "unique_zones": len({r.shipping_zone_id for r in rates}),
        "unique_regions": len({r.warehouse_region for r in rates}),
        "unique_service_levels": len({r.service_level for r in rates}),
        "min_price_pln": min(prices) if prices else 0,
        "max_price_pln": max(prices) if prices else 0,
        "average_price_pln": round(sum(prices) / len(prices), 4) if prices else 0,
    }


@router.get("/by-zone/{zone_id}", response_model=List[ShippingRateResponse])
# Admin: list shipping rates by zone
async def get_rates_by_zone_admin(
    zone_id: int = Path(..., gt=0, description="Shipping zone ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    zone = db.query(ShippingZone).filter(ShippingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Shipping zone with ID {zone_id} not found")
    rates = (
        db.query(ShippingRate)
        .filter(ShippingRate.shipping_zone_id == zone_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rates


@router.get("/by-region/{region}", response_model=List[ShippingRateResponse])
# Admin: list shipping rates by region
async def get_rates_by_region_admin(
    region: str = Path(..., min_length=1, max_length=200, description="Warehouse region"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rates = (
        db.query(ShippingRate)
        .filter(ShippingRate.warehouse_region.ilike(f"%{region}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rates


@router.get("/search", response_model=List[ShippingRateResponse])
# Admin: search shipping rates by carrier
async def search_shipping_rates_admin(
    carrier: str = Query(..., min_length=1, max_length=100, description="Carrier substring"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rates = (
        db.query(ShippingRate)
        .filter(ShippingRate.carrier.ilike(f"%{carrier}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rates


@router.get("/find-rate", response_model=List[ShippingRateResponse])
# Admin: find shipping rates matching zone/weight/carrier
async def find_shipping_rates_admin(
    zone_id: int = Query(..., gt=0, description="Shipping zone ID"),
    weight: float = Query(..., gt=0, description="Weight to check (in kg or lbs)"),
    carrier: Optional[str] = Query(None, description="Optional: filter by carrier substring"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    zone = db.query(ShippingZone).filter(ShippingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Shipping zone with ID {zone_id} not found")

    query = db.query(ShippingRate).filter(
        ShippingRate.shipping_zone_id == zone_id,
        ShippingRate.weight_min <= weight,
        ShippingRate.weight_max >= weight,
    )
    if carrier:
        query = query.filter(ShippingRate.carrier.ilike(f"%{carrier}%"))

    rates = query.offset(skip).limit(limit).all()
    return rates
