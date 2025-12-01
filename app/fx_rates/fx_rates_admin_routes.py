from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
from typing import List
from datetime import datetime
from decimal import Decimal

from app.fx_rates.fx_rates_schema import (
    FxRateCreate,
    FxRateUpdate,
    FxRateResponse,
)
from app.fx_rates.fx_rates_model import FxRate
from db_routers_connection import get_db


router = APIRouter(prefix="/api/fxrates/admin", tags=["fxrates-admin"]) 


@router.get("/", response_model=List[FxRateResponse])
# Admin: list FX rates
async def list_fxrates_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    fxrates = db.query(FxRate).offset(skip).limit(limit).all()
    return fxrates


@router.post("/", response_model=FxRateResponse, status_code=201)
# Admin: create FX rate
async def create_fxrate(
    fxrate: FxRateCreate, db: Session = Depends(get_db)
):
    from_curr = fxrate.from_currency.upper()
    to_curr = fxrate.to_currency.upper()

    existing = db.query(FxRate).filter(
        FxRate.from_currency == from_curr, FxRate.to_currency == to_curr
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Exchange rate for {from_curr}/{to_curr} already exists (ID: {existing.id})",
        )

    db_fxrate = FxRate(
        from_currency=from_curr,
        to_currency=to_curr,
        rate=fxrate.rate,
        updated_at=datetime.utcnow(),
    )
    db.add(db_fxrate)
    db.commit()
    db.refresh(db_fxrate)

    return db_fxrate


@router.get("/{fxrate_id}", response_model=FxRateResponse)
# Admin: get FX rate detail
async def get_fxrate_admin(
    fxrate_id: int = Path(..., gt=0, description="FX Rate ID"),
    db: Session = Depends(get_db),
):
    fxrate = db.query(FxRate).filter(FxRate.id == fxrate_id).first()

    if not fxrate:
        raise HTTPException(status_code=404, detail=f"FX Rate with ID {fxrate_id} not found")

    return fxrate


@router.put("/{fxrate_id}", response_model=FxRateResponse)
# Admin: update FX rate
async def update_fxrate(
    fxrate_id: int = Path(..., gt=0, description="FX Rate ID"),
    fxrate_update: FxRateUpdate = None,
    db: Session = Depends(get_db),
):
    db_fxrate = db.query(FxRate).filter(FxRate.id == fxrate_id).first()

    if not db_fxrate:
        raise HTTPException(status_code=404, detail=f"FX Rate with ID {fxrate_id} not found")

    from_curr = db_fxrate.from_currency
    to_curr = db_fxrate.to_currency

    if fxrate_update.from_currency:
        from_curr = fxrate_update.from_currency.upper()

    if fxrate_update.to_currency:
        to_curr = fxrate_update.to_currency.upper()

    if from_curr != db_fxrate.from_currency or to_curr != db_fxrate.to_currency:
        existing = (
            db.query(FxRate)
            .filter(
                FxRate.from_currency == from_curr,
                FxRate.to_currency == to_curr,
                FxRate.id != fxrate_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Exchange rate for {from_curr}/{to_curr} already exists",
            )

    if fxrate_update.from_currency:
        db_fxrate.from_currency = from_curr

    if fxrate_update.to_currency:
        db_fxrate.to_currency = to_curr

    if fxrate_update.rate:
        db_fxrate.rate = fxrate_update.rate

    if fxrate_update.updated_at:
        db_fxrate.updated_at = fxrate_update.updated_at
    else:
        db_fxrate.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_fxrate)

    return db_fxrate


@router.delete("/{fxrate_id}", status_code=204)
# Admin: delete FX rate
async def delete_fxrate(
    fxrate_id: int = Path(..., gt=0, description="FX Rate ID"),
    db: Session = Depends(get_db),
):
    db_fxrate = db.query(FxRate).filter(FxRate.id == fxrate_id).first()

    if not db_fxrate:
        raise HTTPException(status_code=404, detail=f"FX Rate with ID {fxrate_id} not found")

    db.delete(db_fxrate)
    db.commit()


@router.post("/bulk-create", response_model=dict, status_code=201)
# Admin: bulk create FX rates
async def bulk_create_fxrates(
    fxrates_data: List[FxRateCreate], db: Session = Depends(get_db)
):
    created = 0
    failed = 0
    errors = []
    fxrates_to_insert = []

    for idx, fxrate_data in enumerate(fxrates_data):
        try:
            from_curr = fxrate_data.from_currency.upper()
            to_curr = fxrate_data.to_currency.upper()

            existing = (
                db.query(FxRate)
                .filter(FxRate.from_currency == from_curr, FxRate.to_currency == to_curr)
                .first()
            )
            if existing:
                errors.append(
                    f"Row {idx + 1}: Exchange rate for {from_curr}/{to_curr} already exists"
                )
                failed += 1
                continue

            fxrates_to_insert.append(
                FxRate(
                    from_currency=from_curr,
                    to_currency=to_curr,
                    rate=fxrate_data.rate,
                    updated_at=datetime.utcnow(),
                )
            )
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    if fxrates_to_insert:
        db.add_all(fxrates_to_insert)
        db.commit()
        created = len(fxrates_to_insert)

    return {
        "created": created,
        "failed": failed,
        "total": len(fxrates_data),
        "errors": errors if errors else None,
    }


@router.post("/bulk-delete", response_model=dict)
# Admin: bulk delete FX rates
async def bulk_delete_fxrates(
    fxrate_ids: List[int] = Query(..., description="List of FX Rate IDs to delete"),
    db: Session = Depends(get_db),
):
    deleted = 0
    failed = 0
    errors = []

    for fxrate_id in fxrate_ids:
        try:
            db_fxrate = db.query(FxRate).filter(FxRate.id == fxrate_id).first()

            if not db_fxrate:
                errors.append(f"ID {fxrate_id}: FX Rate not found")
                failed += 1
                continue

            db.delete(db_fxrate)
            deleted += 1
        except Exception as e:
            errors.append(f"ID {fxrate_id}: {str(e)}")
            failed += 1

    db.commit()

    return {
        "deleted": deleted,
        "failed": failed,
        "total": len(fxrate_ids),
        "errors": errors if errors else None,
    }


@router.put("/update-rate", response_model=FxRateResponse)
# Admin: update FX rate value
async def update_fxrate_value(
    from_currency: str = Query(..., min_length=3, max_length=3, description="Source currency code"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Target currency code"),
    new_rate: Decimal = Query(..., gt=0, description="New exchange rate"),
    db: Session = Depends(get_db),
):
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    db_fxrate = (
        db.query(FxRate)
        .filter(FxRate.from_currency == from_curr, FxRate.to_currency == to_curr)
        .first()
    )

    if not db_fxrate:
        raise HTTPException(status_code=404, detail=f"Exchange rate for {from_curr}/{to_curr} not found")

    db_fxrate.rate = new_rate
    db_fxrate.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_fxrate)

    return db_fxrate


@router.get("/statistics", response_model=dict)
# Admin: FX rates statistics
async def get_fxrates_statistics(db: Session = Depends(get_db)):
    total_rates = db.query(FxRate).count()

    currencies = db.query(FxRate.from_currency).distinct().count()

    min_rate = db.query(func.min(FxRate.rate)).scalar() or 0
    max_rate = db.query(func.max(FxRate.rate)).scalar() or 0
    avg_rate = db.query(func.avg(FxRate.rate)).scalar() or 0

    return {
        "total_exchange_rates": total_rates,
        "unique_source_currencies": currencies,
        "min_rate": float(min_rate) if min_rate else 0,
        "max_rate": float(max_rate) if max_rate else 0,
        "average_rate": round(float(avg_rate), 6) if avg_rate else 0,
    }


@router.get("/rate-pairs", response_model=dict)
# Admin: list FX rate pairs summary
async def get_fxrate_pairs_summary(db: Session = Depends(get_db)):
    pairs = db.query(
        FxRate.from_currency, FxRate.to_currency, FxRate.rate, FxRate.updated_at
    ).all()

    grouped = {}
    for from_curr, to_curr, rate, updated_at in pairs:
        key = f"{from_curr}/{to_curr}"
        grouped[key] = {
            "rate": float(rate),
            "updated_at": updated_at.isoformat() if updated_at else None,
        }

    return {"total_pairs": len(grouped), "pairs": grouped}
