from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from typing import List

from app.subcategories.subcategories_schema import SubcategoryResponse
from app.subcategories.subcategories_model import Subcategory
from app.categories.categories_model import Category
from app.parts.parts_model import Part
from db_routers_connection import get_db


router = APIRouter(prefix="/api/subcategories", tags=["subcategories-public"]) 


@router.get("/", response_model=List[SubcategoryResponse])
# Public: list subcategories
async def list_subcategories(
    skip: int = Query(0, ge=0, description="Pagination: skip N results"),
    limit: int = Query(50, ge=1, le=500, description="Pagination: max results (default 50, max 500)"),
    db: Session = Depends(get_db)
):
    subcategories = db.query(Subcategory).offset(skip).limit(limit).all()
    return subcategories


@router.get("/search", response_model=List[SubcategoryResponse])
# Public: search subcategories by name
async def search_subcategories(
    name: str = Query(..., min_length=1, max_length=100, description="Subcategory name to search (substring)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    subcategories = db.query(Subcategory).filter(
        Subcategory.name.ilike(f"%{name}%")
    ).offset(skip).limit(limit).all()
    
    return subcategories


@router.get("/by-parent/{parent_id}", response_model=List[SubcategoryResponse])
# Public: list subcategories by parent category
async def get_subcategories_by_parent(
    parent_id: int = Path(..., gt=0, description="Parent category ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == parent_id).first()
    
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Parent category with ID {parent_id} not found"
        )
    
    subcategories = db.query(Subcategory).filter(
        Subcategory.parent_id == parent_id
    ).offset(skip).limit(limit).all()
    
    return subcategories


@router.get("/{subcategory_id}", response_model=SubcategoryResponse)
# Public: get subcategory detail
async def get_subcategory(
    subcategory_id: int = Path(..., gt=0, description="Subcategory ID"),
    db: Session = Depends(get_db)
):
    subcategory = db.query(Subcategory).filter(Subcategory.id == subcategory_id).first()
    
    if not subcategory:
        raise HTTPException(
            status_code=404,
            detail=f"Subcategory with ID {subcategory_id} not found"
        )
    
    return subcategory


@router.get("/{subcategory_id}/parts-count", response_model=dict)
# Public: subcategory parts count
async def get_subcategory_parts_count(
    subcategory_id: int = Path(..., gt=0, description="Subcategory ID"),
    db: Session = Depends(get_db)
):
    subcategory = db.query(Subcategory).filter(Subcategory.id == subcategory_id).first()
    
    if not subcategory:
        raise HTTPException(
            status_code=404,
            detail=f"Subcategory with ID {subcategory_id} not found"
        )
    
    parts_count = db.query(Part).filter(Part.subcategory_id == subcategory_id).count()
    
    return {
        "subcategory_id": subcategory.id,
        "subcategory_name": subcategory.name,
        "parent_id": subcategory.parent_id,
        "total_parts": parts_count
    }
