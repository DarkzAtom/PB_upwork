from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from typing import List

from schemas.schemas import (
    SubcategoryCreate,
    SubcategoryUpdate,
    SubcategoryResponse,
)
from models import Subcategory, Category, Part
from db_connection import engine

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/subcategories/admin", tags=["subcategories-admin"])


@router.get("/all", response_model=List[SubcategoryResponse])
# Admin: list subcategories
async def list_all_subcategories_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    subcategories = db.query(Subcategory).offset(skip).limit(limit).all()
    return subcategories


@router.post("/", response_model=SubcategoryResponse, status_code=201)
# Admin: create subcategory
async def create_subcategory(
    subcategory: SubcategoryCreate,
    db: Session = Depends(get_db),
):
    parent = db.query(Category).filter(Category.id == subcategory.parent_id).first()

    if not parent:
        raise HTTPException(
            status_code=404,
            detail=f"Parent category with ID {subcategory.parent_id} not found",
        )

    existing = (
        db.query(Subcategory)
        .filter(
            Subcategory.name == subcategory.name,
            Subcategory.parent_id == subcategory.parent_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Subcategory name '{subcategory.name}' already exists under category ID {subcategory.parent_id} "
                f"(Subcategory ID: {existing.id})"
            ),
        )

    db_subcategory = Subcategory(**subcategory.dict())
    db.add(db_subcategory)
    db.commit()
    db.refresh(db_subcategory)

    return db_subcategory


@router.get("/{subcategory_id}", response_model=SubcategoryResponse)
# Admin: get subcategory detail
async def get_subcategory_admin(
    subcategory_id: int = Path(..., gt=0, description="Subcategory ID"),
    db: Session = Depends(get_db),
):
    subcategory = db.query(Subcategory).filter(Subcategory.id == subcategory_id).first()

    if not subcategory:
        raise HTTPException(
            status_code=404,
            detail=f"Subcategory with ID {subcategory_id} not found",
        )

    return subcategory


@router.put("/{subcategory_id}", response_model=SubcategoryResponse)
# Admin: update subcategory
async def update_subcategory(
    subcategory_id: int = Path(..., gt=0, description="Subcategory ID"),
    subcategory_update: SubcategoryUpdate = None,
    db: Session = Depends(get_db),
):
    db_subcategory = db.query(Subcategory).filter(Subcategory.id == subcategory_id).first()

    if not db_subcategory:
        raise HTTPException(
            status_code=404,
            detail=f"Subcategory with ID {subcategory_id} not found",
        )

    if subcategory_update.parent_id and subcategory_update.parent_id != db_subcategory.parent_id:
        parent = db.query(Category).filter(Category.id == subcategory_update.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=404,
                detail=f"Parent category with ID {subcategory_update.parent_id} not found",
            )

    if subcategory_update.name and subcategory_update.name != db_subcategory.name:
        parent_id = subcategory_update.parent_id or db_subcategory.parent_id
        existing = (
            db.query(Subcategory)
            .filter(
                Subcategory.name == subcategory_update.name,
                Subcategory.parent_id == parent_id,
                Subcategory.id != subcategory_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Subcategory name '{subcategory_update.name}' already exists under category ID {parent_id}",
            )

    update_data = subcategory_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_subcategory, key, value)

    db.commit()
    db.refresh(db_subcategory)

    return db_subcategory


@router.delete("/{subcategory_id}", status_code=204)
# Admin: delete subcategory
async def delete_subcategory(
    subcategory_id: int = Path(..., gt=0, description="Subcategory ID"),
    force: bool = Query(False, description="Force delete even if parts exist"),
    db: Session = Depends(get_db),
):
    db_subcategory = db.query(Subcategory).filter(Subcategory.id == subcategory_id).first()

    if not db_subcategory:
        raise HTTPException(
            status_code=404,
            detail=f"Subcategory with ID {subcategory_id} not found",
        )

    parts_count = db.query(Part).filter(Part.subcategory_id == subcategory_id).count()

    if parts_count > 0 and not force:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete subcategory: has {parts_count} parts. Use force=true to delete anyway.",
        )

    db.delete(db_subcategory)
    db.commit()


@router.post("/bulk-create", response_model=dict, status_code=201)
# Admin: bulk create subcategories
async def bulk_create_subcategories(
    subcategories_data: List[SubcategoryCreate],
    db: Session = Depends(get_db),
):
    created = 0
    failed = 0
    errors = []
    subcategories_to_insert = []

    for idx, subcategory_data in enumerate(subcategories_data):
        try:
            parent = db.query(Category).filter(Category.id == subcategory_data.parent_id).first()
            if not parent:
                errors.append(
                    f"Row {idx + 1}: Parent category with ID {subcategory_data.parent_id} not found"
                )
                failed += 1
                continue

            existing = (
                db.query(Subcategory)
                .filter(
                    Subcategory.name == subcategory_data.name,
                    Subcategory.parent_id == subcategory_data.parent_id,
                )
                .first()
            )
            if existing:
                errors.append(
                    f"Row {idx + 1}: Subcategory name '{subcategory_data.name}' already exists under category ID {subcategory_data.parent_id}"
                )
                failed += 1
                continue

            subcategories_to_insert.append(Subcategory(**subcategory_data.dict()))
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    if subcategories_to_insert:
        db.add_all(subcategories_to_insert)
        db.commit()
        created = len(subcategories_to_insert)

    return {
        "created": created,
        "failed": failed,
        "total": len(subcategories_data),
        "errors": errors if errors else None,
    }


@router.post("/bulk-delete", response_model=dict, status_code=200)
# Admin: bulk delete subcategories
async def bulk_delete_subcategories(
    subcategory_ids: List[int] = Query(..., description="List of subcategory IDs to delete"),
    force: bool = Query(False, description="Force delete even if parts exist"),
    db: Session = Depends(get_db),
):
    deleted = 0
    failed = 0
    errors = []

    for subcategory_id in subcategory_ids:
        try:
            db_subcategory = db.query(Subcategory).filter(Subcategory.id == subcategory_id).first()

            if not db_subcategory:
                errors.append(f"ID {subcategory_id}: Subcategory not found")
                failed += 1
                continue

            parts_count = db.query(Part).filter(Part.subcategory_id == subcategory_id).count()

            if parts_count > 0 and not force:
                errors.append(f"ID {subcategory_id}: Has {parts_count} parts. Set force=true to delete")
                failed += 1
                continue

            db.delete(db_subcategory)
            deleted += 1
        except Exception as e:
            errors.append(f"ID {subcategory_id}: {str(e)}")
            failed += 1

    db.commit()

    return {
        "deleted": deleted,
        "failed": failed,
        "total": len(subcategory_ids),
        "errors": errors if errors else None,
    }


@router.put("/{subcategory_id}/move-to-parent", response_model=SubcategoryResponse)
# Admin: move subcategory to different parent
async def move_subcategory_to_parent(
    subcategory_id: int = Path(..., gt=0, description="Subcategory ID"),
    new_parent_id: int = Query(..., gt=0, description="New parent category ID"),
    db: Session = Depends(get_db),
):
    db_subcategory = db.query(Subcategory).filter(Subcategory.id == subcategory_id).first()

    if not db_subcategory:
        raise HTTPException(
            status_code=404,
            detail=f"Subcategory with ID {subcategory_id} not found",
        )

    new_parent = db.query(Category).filter(Category.id == new_parent_id).first()
    if not new_parent:
        raise HTTPException(
            status_code=404,
            detail=f"Parent category with ID {new_parent_id} not found",
        )

    if new_parent_id == db_subcategory.parent_id:
        raise HTTPException(
            status_code=400,
            detail=f"Subcategory already belongs to category ID {new_parent_id}",
        )

    existing = (
        db.query(Subcategory)
        .filter(Subcategory.name == db_subcategory.name, Subcategory.parent_id == new_parent_id)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Subcategory name '{db_subcategory.name}' already exists under category ID {new_parent_id}",
        )

    db_subcategory.parent_id = new_parent_id
    db.commit()
    db.refresh(db_subcategory)

    return db_subcategory


@router.get("/statistics", response_model=dict)
# Admin: subcategories statistics
async def get_subcategories_statistics(
    db: Session = Depends(get_db),
):
    total = db.query(Subcategory).count()

    total_parts = db.query(Part).count()

    categories = db.query(Category).count()

    subcategories_with_parts = db.query(Subcategory).join(
        Part, Subcategory.id == Part.subcategory_id
    ).count()

    return {
        "total_subcategories": total,
        "total_categories": categories,
        "total_parts": total_parts,
        "subcategories_with_parts": subcategories_with_parts,
        "subcategories_without_parts": total - subcategories_with_parts,
    }
