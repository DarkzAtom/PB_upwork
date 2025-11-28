from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from typing import List

from db_connection import engine
from PB_upwork.app.brands.brands_model import Brand
from PB_upwork.app.brands.brands_schema import BrandResponse

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/brands", tags=["brands-public"])


@router.get("/", response_model=List[BrandResponse])
# Public: list brands
def list_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return db.query(Brand).offset(skip).limit(limit).all()


@router.get("/search", response_model=List[BrandResponse])
# Public: search brands by name
def search_brands(
    name: str = Query(..., min_length=1, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return (
        db.query(Brand)
        .filter(Brand.name.ilike(f"%{name}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{brand_id}", response_model=BrandResponse)
# Public: get brand detail
def get_brand(
    brand_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand
