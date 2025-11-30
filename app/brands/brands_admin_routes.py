from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
from typing import List

from db_connection import engine
from app.brands.brands_model import Brand
from app.parts.parts_model import Part
from app.brands.brands_schema import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
)

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/brands/admin", tags=["brands-admin"])


@router.get("", response_model=List[BrandResponse])
# Admin: list brands
def list_brands_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return db.query(Brand).offset(skip).limit(limit).all()


@router.post("", response_model=BrandResponse, status_code=201)
# Admin: create brand
def create_brand(
    brand: BrandCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(Brand).filter(Brand.name == brand.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Brand name '{brand.name}' already exists (ID: {existing.id})")

    db_brand = Brand(**brand.dict())
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    return db_brand


@router.get("/{brand_id}", response_model=BrandResponse)
# Admin: get brand detail
def get_brand_admin(
    brand_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.put("/{brand_id}", response_model=BrandResponse)
# Admin: update brand
def update_brand(
    brand_id: int = Path(..., gt=0),
    brand_update: BrandUpdate = None,
    db: Session = Depends(get_db),
):
    db_brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not db_brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    if brand_update and brand_update.name and brand_update.name != db_brand.name:
        existing = db.query(Brand).filter(Brand.name == brand_update.name).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Brand name '{brand_update.name}' already exists")

    update_data = brand_update.dict(exclude_unset=True) if brand_update else {}
    for key, value in update_data.items():
        setattr(db_brand, key, value)

    db.commit()
    db.refresh(db_brand)
    return db_brand


@router.delete("/{brand_id}", status_code=204)
# Admin: delete brand
def delete_brand(
    brand_id: int = Path(..., gt=0),
    force: bool = Query(False),
    db: Session = Depends(get_db),
):
    db_brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not db_brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    parts_count = db.query(Part).filter(Part.brand_id == db_brand.id).count()
    if parts_count > 0 and not force:
        raise HTTPException(status_code=409, detail="Cannot delete brand with existing parts without force=true")

    db.delete(db_brand)
    db.commit()
    return None


@router.post("/bulk-create", response_model=dict, status_code=201)
# Admin: bulk create brands
def bulk_create_brands(
    brands_data: List[BrandCreate],
    db: Session = Depends(get_db),
):
    created = 0
    failed = 0
    errors: List[str] = []
    to_insert: List[Brand] = []

    for idx, data in enumerate(brands_data):
        try:
            existing = db.query(Brand).filter(Brand.name == data.name).first()
            if existing:
                raise ValueError(f"Row {idx + 1}: Brand name '{data.name}' already exists (ID: {existing.id})")
            to_insert.append(Brand(**data.dict()))
            created += 1
        except Exception as e:
            errors.append(str(e))
            failed += 1

    if to_insert:
        db.add_all(to_insert)
        db.commit()

    return {
        "total": len(brands_data),
        "created": created,
        "failed": failed,
        "errors": errors,
        "message": f"Created {created} brands, {failed} failed",
    }


@router.get("/bulk-delete", response_model=dict)
# Admin: bulk delete brands
def bulk_delete_brands(
    ids: List[int] = Query(..., description="Brand IDs to delete"),
    force: bool = Query(False, description="Force delete even if parts exist"),
    db: Session = Depends(get_db),
):
    if not ids:
        raise HTTPException(status_code=400, detail="No brand IDs provided")

    deleted = 0
    failed = 0
    errors: List[str] = []

    for brand_id in ids:
        try:
            db_brand = db.query(Brand).filter(Brand.id == brand_id).first()
            if not db_brand:
                errors.append(f"Brand ID {brand_id} not found")
                failed += 1
                continue

            parts_count = db.query(Part).filter(Part.brand_id == db_brand.id).count()
            if parts_count > 0 and not force:
                errors.append(f"Brand ID {brand_id} ({db_brand.name}) has {parts_count} parts")
                failed += 1
                continue

            db.delete(db_brand)
            deleted += 1
        except Exception as e:
            errors.append(f"Brand ID {brand_id}: {str(e)}")
            failed += 1

    db.commit()
    return {
        "total": len(ids),
        "deleted": deleted,
        "failed": failed,
        "errors": errors,
        "message": f"Deleted {deleted} brands, {failed} failed",
    }


@router.get("/stats", response_model=dict)
# Admin: brand statistics
def get_brand_statistics(db: Session = Depends(get_db)):
    total_brands = db.query(Brand).count()

    brands_with_counts = (
        db.query(Brand.id, Brand.name, func.count(Part.id).label("parts_count"))
        .outerjoin(Part, Part.brand_id == Brand.id)
        .group_by(Brand.id, Brand.name)
        .all()
    )

    brands_with_parts = sum(1 for b in brands_with_counts if b.parts_count > 0)
    brands_without_parts = total_brands - brands_with_parts
    total_parts = sum(b.parts_count for b in brands_with_counts)
    avg_parts = total_parts / total_brands if total_brands > 0 else 0

    top_5 = sorted(brands_with_counts, key=lambda x: x.parts_count, reverse=True)[:5]

    return {
        "total_brands": total_brands,
        "brands_with_parts": brands_with_parts,
        "brands_without_parts": brands_without_parts,
        "total_parts_count": total_parts,
        "avg_parts_per_brand": round(avg_parts, 2),
        "top_5_brands": [
            {"brand_id": b.id, "name": b.name, "parts_count": b.parts_count} for b in top_5
        ],
    }
