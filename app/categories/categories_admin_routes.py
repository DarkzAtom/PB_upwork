from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
from typing import List

from app.categories.categories_schema import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from app.categories.categories_model import Category
from app.subcategories.subcategories_model import Subcategory
from app.parts.parts_model import Part

from db_routers_connection import get_db


router = APIRouter(prefix="/api/categories/admin", tags=["categories-admin"]) 


@router.get("/", response_model=List[CategoryResponse])
# Admin: list categories
async def list_all_categories_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories


@router.post("/", response_model=CategoryResponse, status_code=201)
# Admin: create category
async def create_category(
    category: CategoryCreate, db: Session = Depends(get_db)
):
    existing = db.query(Category).filter(Category.name == category.name).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Category name '{category.name}' already exists (ID: {existing.id})",
        )

    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category


@router.get("/{category_id}", response_model=CategoryResponse)
# Admin: get category detail
async def get_category_admin(
    category_id: int = Path(..., gt=0, description="Category ID"),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
# Admin: update category
async def update_category(
    category_id: int = Path(..., gt=0, description="Category ID"),
    category_update: CategoryUpdate = None,
    db: Session = Depends(get_db),
):
    db_category = db.query(Category).filter(Category.id == category_id).first()

    if not db_category:
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")

    if category_update.name and category_update.name != db_category.name:
        existing = db.query(Category).filter(Category.name == category_update.name).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Category name '{category_update.name}' already exists",
            )

    update_data = category_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)

    return db_category


@router.delete("/{category_id}", status_code=204)
# Admin: delete category
async def delete_category(
    category_id: int = Path(..., gt=0, description="Category ID"),
    force: bool = Query(False, description="Force delete even if parts/subcategories exist"),
    db: Session = Depends(get_db),
):
    db_category = db.query(Category).filter(Category.id == category_id).first()

    if not db_category:
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")

    subcategories_count = db.query(Subcategory).filter(Subcategory.parent_id == category_id).count()
    parts_count = db.query(Part).filter(Part.category_id == category_id).count()

    if (subcategories_count > 0 or parts_count > 0) and not force:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete category: has {subcategories_count} subcategories and {parts_count} parts. "
                f"Use force=true to delete anyway."
            ),
        )

    db.delete(db_category)
    db.commit()


@router.post("/bulk-create", response_model=dict, status_code=201)
# Admin: bulk create categories
async def bulk_create_categories(
    categories_data: List[CategoryCreate], db: Session = Depends(get_db)
):
    created = 0
    failed = 0
    errors = []
    categories_to_insert = []

    for idx, category_data in enumerate(categories_data):
        try:
            existing = db.query(Category).filter(Category.name == category_data.name).first()
            if existing:
                errors.append(
                    f"Row {idx + 1}: Category name '{category_data.name}' already exists (ID: {existing.id})"
                )
                failed += 1
                continue

            categories_to_insert.append(Category(**category_data.dict()))
            created += 1

        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    if categories_to_insert:
        db.add_all(categories_to_insert)
        db.commit()

    return {
        "total": len(categories_data),
        "created": created,
        "failed": failed,
        "errors": errors,
        "message": f"Created {created} categories, {failed} failed",
    }


@router.get("/bulk-delete", response_model=dict)
# Admin: bulk delete categories
async def bulk_delete_categories(
    ids: List[int] = Query(..., description="List of category IDs to delete"),
    force: bool = Query(False, description="Force delete even if parts/subcategories exist"),
    db: Session = Depends(get_db),
):
    if not ids:
        raise HTTPException(status_code=400, detail="No category IDs provided")

    deleted = 0
    failed = 0
    errors = []

    for category_id in ids:
        try:
            db_category = db.query(Category).filter(Category.id == category_id).first()

            if not db_category:
                errors.append(f"Category ID {category_id} not found")
                failed += 1
                continue

            subcategories_count = db.query(Subcategory).filter(Subcategory.parent_id == category_id).count()
            parts_count = db.query(Part).filter(Part.category_id == category_id).count()

            if (subcategories_count > 0 or parts_count > 0) and not force:
                errors.append(
                    f"Category ID {category_id} ({db_category.name}) has {subcategories_count} subcategories and {parts_count} parts"
                )
                failed += 1
                continue

            db.delete(db_category)
            deleted += 1

        except Exception as e:
            errors.append(f"Category ID {category_id}: {str(e)}")
            failed += 1

    db.commit()

    return {
        "total": len(ids),
        "deleted": deleted,
        "failed": failed,
        "errors": errors,
        "message": f"Deleted {deleted} categories, {failed} failed",
    }


@router.get("/stats", response_model=dict)
# Admin: category statistics
async def get_category_statistics(db: Session = Depends(get_db)):
    total_categories = db.query(Category).count()

    categories_with_counts = (
        db.query(
            Category.id,
            Category.name,
            func.count(Part.id).label("parts_count"),
        )
        .outerjoin(Part, Category.id == Part.category_id)
        .group_by(Category.id, Category.name)
        .all()
    )

    categories_with_parts = sum(1 for c in categories_with_counts if c.parts_count > 0)
    categories_without_parts = total_categories - categories_with_parts
    total_parts = sum(c.parts_count for c in categories_with_counts)
    avg_parts = total_parts / total_categories if total_categories > 0 else 0

    total_subcategories = db.query(Subcategory).count()
    avg_subcategories = total_subcategories / total_categories if total_categories > 0 else 0

    top_5 = sorted(categories_with_counts, key=lambda x: x.parts_count, reverse=True)[:5]

    return {
        "total_categories": total_categories,
        "categories_with_parts": categories_with_parts,
        "categories_without_parts": categories_without_parts,
        "total_parts_count": total_parts,
        "avg_parts_per_category": round(avg_parts, 2),
        "total_subcategories": total_subcategories,
        "avg_subcategories_per_category": round(avg_subcategories, 2),
        "top_5_categories": [
            {"category_id": c.id, "name": c.name, "parts_count": c.parts_count}
            for c in top_5
        ],
    }
