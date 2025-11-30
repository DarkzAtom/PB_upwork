from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
from typing import List

from app.categories.categories_schema import CategoryResponse
from app.subcategories.subcategories_schema import SubcategoryResponse
from app.categories.categories_model import Category
from app.subcategories.subcategories_model import Subcategory
from app.parts.parts_model import Part
from db_connection import engine

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/categories", tags=["categories-public"]) 


@router.get("/", response_model=List[CategoryResponse])
# Public: list categories
async def list_categories(
    skip: int = Query(0, ge=0, description="Pagination: skip N results"),
    limit: int = Query(50, ge=1, le=500, description="Pagination: max results (default 50, max 500)"),
    db: Session = Depends(get_db),
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories


@router.get("/search", response_model=List[CategoryResponse])
# Public: search categories by name
async def search_categories(
    name: str = Query(..., min_length=1, max_length=100, description="Category name to search (substring)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    categories = (
        db.query(Category)
        .filter(Category.name.ilike(f"%{name}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
# Public: get category detail
async def get_category(
    category_id: int = Path(..., gt=0, description="Category ID"),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")

    return category


@router.get("/{category_id}/subcategories", response_model=List[SubcategoryResponse])
# Public: list subcategories of category
async def get_category_subcategories(
    category_id: int = Path(..., gt=0, description="Category ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")

    subcategories = (
        db.query(Subcategory)
        .filter(Subcategory.parent_id == category_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return subcategories


@router.get("/{category_id}/parts-count", response_model=dict)
# Public: category parts/subcategories counts
async def get_category_parts_count(
    category_id: int = Path(..., gt=0, description="Category ID"),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")

    parts_count = db.query(func.count(Part.id)).filter(Part.category_id == category_id).scalar() or 0
    subcategories_count = db.query(func.count(Subcategory.id)).filter(Subcategory.parent_id == category_id).scalar() or 0

    return {
        "category_id": category.id,
        "category_name": category.name,
        "total_parts": parts_count,
        "total_subcategories": subcategories_count,
    }
