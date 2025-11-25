from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_session
from typing import List, Optional
from decimal import Decimal
from PB_upwork.schemas.schemas import (
    PartBasic,
    PartCreate,
    PartUpdate,
    PartDetail,
    PartResponse,
    PartAdmin,
)
from models import (
    Part, 
    Brand, 
    Category, 
    Subcategory, 
    Supplier,
    SupplierPrice,
)
from db_connection import engine

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="api/parts", tags=["parts"])

@router.get("search/", response_model=List[PartBasic])
async def search_parts(
    brand: Optional[str] = Query(None, min_length=1, max_length=100),
    category: Optional[str] = Query(None, min_length=1, max_length=100),
    part_name: Optional[str] = Query(None, min_length=1, max_length=200),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Part)

    if brand:
        query = query.filter(Part.brand.ilike(f"%{brand}%"))
    if category:
        query = query.join(Category).filter(Category.name.ilike(f"%{category}%"))
    if part_name:
        query = query.filter(Part.name.ilike(f"%{part_name}%"))

    total_count = query.count()

    parts = query.offset(skip).limit(limit).all()

    if not parts:
        return []
    
    return [
        PartBasic(
            id=part.id,
            brand=part.brand,
            part_number=part.part_number,
            name=part.name,
            images=part.images,
        )
        for part in parts
    ]

@router.get("/{part_id}", response_model=PartDetail)
async def get_part_detail(
    part_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
    ):
    part = db.query(Part).filter(Part.id == part_id).first()

    if not part:
        raise HTTPException(
            status_code=404,
              detail="Part not found"
            )
    
    return PartDetail(
        id=part.id,
        brand=part.brand,
        part_number=part.part_number,
        name=part.name,
        description=part.decription,
        category_id=part.category_id,
        subcategory_id=part.subcategory_id,
        images=part.images,
        attributes=part.attributes,
        vehicle_fitment=part.vehicle_fitment,
    )

@router.get("/admin/{part_id}", response_model=List[PartResponse])
async def get_all_parts_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    supplier_id: Optional[int] = Query(None, gt=0),
    category_id: Optional[int] = Query(None, gt=0),
    db: Session = Depends(get_db)
):
    query = db.query(Part)

    if supplier_id:
        query = query.filter(Part.supplier_id == supplier_id)

    if category_id:
        query = query.filter(Part.category_id == category_id)

    parts = query.offset(skip).limit(limit).all()

    return parts

@router.post("/admin", response_model=PartResponse,  status_code=201)
async def create_part_admin(
    part: PartCreate,
    db: Session = Depends(get_db)
):
    supplier = db.query(Suplier).filter(
        Supplier.id == part.supplier_id
    ).first()
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    category = db.query(Category).filter(
        Category.id == part.category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    
    subcategory = db.query(Subcategory).filter(
        Subcategory.id == part.subcategory_id
    ).first()
    if not subcategory:
        raise HTTPException(
            status_code=404,
            detail="Subcategory not found"
        )
    
    existing = db.query(Part).filter(
        Part.part_number == part.part_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Part with this part number already exists"
        )
    
    db_part = Part(
        **part.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_part)
    db.commit()
    db.refresh(db_part)

    return PartResponse(
        id=db_part.id,
        supplier_id=db_part.supplier_id,
        supplier_part_id=db_part.supplier_part_id,
        brand=db_part.brand,
        part_number=db_part.part_number,
        name=db_part.name,
        description=db_part.decription,
        category_id=db_part.category_id,
        subcategory_id=db_part.subcategory_id,
        images=db_part.images,
        attributes=db_part.attributes,
        vehicle_fitment=db_part.vehicle_fitment,
        created_at=db_part.created_at,
        updated_at=db_part.updated_at,
    )

@router.get("/admin/{part_id}", response_model=PartAdmin)
async def get_part_admin(
    part_id: int = Path(..., gt = 0),
    db: Session = Depends(get_db)
):
    part = db.query(Part).filter(Part.id == part_id).first()

    if not part:
        raise HTTPException(
            status_code=404,
            detail="Part not found"
        )
    
    supplier_prices = db.query(SupplierPrice).filter(
        SupplierPrice.part_id == part.id
    ).all()

    cost_prices = None
    if supplier_prices:
        cost_prices = min(sp.base_price for sp in supplier_prices)

    return PartAdmin(
        id=part.id,
        part_number=part.part_number,
        name=part.name,
        brand=part.brand,
        supplier_id=part.supplier_id,
        cost_price=cost_prices,
        margin_percent=None,
        selling_price=None,
    )
        
    

@router.put("/admin/{part_id}", response_model=PartResponse)
async def update_part_admin(
    part_id: int = Path(..., gt=0),
    part_update: PartUpdate = None,
    db: Session = Depends(get_db)
):
    db_part = db.query(Part).filter(Part.id == part_id).first()

    if not db_part:
        raise HTTPException(
            status_code=404,
            detail="Part not found"
        )
    
    if (part_update.part_number and 
        part_update.part_number != db_part.part_number):
        existing = db.query(Part).filter(
            Part.part_number == part_update.part_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Part number '{part_update.part_number}' already exists"
            )
        
    if (part_update.category_id and 
        part_update.category_id != db_part.category_id):
        category = db.query(Category).filter(
            Category.id == part_update.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=404,
                detail=f"Category with ID {part_update.category_id} not found"
            )
        
    update_data = part_update.dict(exclude_unset=True)
    update_data['updated_at'] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(db_part, key, value)

    db.commit()
    db.refresh(db_part)

    return PartResponse(
        id=db_part.id,
        supplier_id=db_part.supplier_id,
        supplier_part_id=db_part.supplier_part_id,
        brand=db_part.brand,
        part_number=db_part.part_number,
        name=db_part.name,
        description=db_part.decription,
        category_id=db_part.category_id,
        subcategory_id=db_part.subcategory_id,
        images=db_part.images,
        attributes=db_part.attributes,
        vehicle_fitment=db_part.vehicle_fitment,
        created_at=db_part.created_at,
        updated_at=db_part.updated_at,
    )

@router.delete("/admin/{part_id}", status_code=204)
async def delete_part_admin(
    part_id: int = Path(..., gt=0, description="Part ID"),
    db: Session = Depends(get_db)
):
     db_part = db.query(Part).filter(Part.id == part_id).first()
    
     if not db_part:
        raise HTTPException(
            status_code=404,
            detail=f"Part with ID {part_id} not found"
        )
     
     db.delete(db_part)
     db.commit()

@router.get("/filter/by-supplier/{supplier_id}", response_model=List[PartBasic])
async def get_parts_by_supplier(
    supplier_id: int = Path(..., gt=0, description="Supplier ID"),
    db: Session = Depends(get_db)
):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id
    ).first()
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier with ID {supplier_id} not found"
        )
    
    parts = db.query(Part).filter(
        Part.supplier_id == supplier_id
    ).all()
    
    return [
        PartBasic(
            id=p.id,
            brand=p.brand,
            part_number=p.part_number,
            name=p.name,
            images=p.images,
        )
        for p in parts
    ]

@router.get("/filter/by-category/{category_id}", response_model=List[PartBasic])
async def get_parts_by_category(
    category_id: int = Path(..., gt=0, description="Category ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Category with ID {category_id} not found"
        )
    
    parts = db.query(Part).filter(
        Part.category_id == category_id
    ).offset(skip).limit(limit).all()
    
    return [
        PartBasic(
            id=p.id,
            brand=p.brand,
            part_number=p.part_number,
            name=p.name,
            images=p.images,
        )
        for p in parts
    ]

@router.post("/admin/bulk-create", response_model=dict)
async def bulk_create_parts(
    parts_data: List[PartCreate],
    db: Session = Depends(get_db)
):
    created = 0
    failed = 0
    errors = []
    parts_to_insert = []
    
    for idx, part_data in enumerate(parts_data):
        try:
            supplier = db.query(Supplier).filter(
                Supplier.id == part_data.supplier_id
            ).first()
            if not supplier:
                errors.append(f"Row {idx}: Supplier ID {part_data.supplier_id} not found")
                failed += 1
                continue
            
            category = db.query(Category).filter(
                Category.id == part_data.category_id
            ).first()
            if not category:
                errors.append(f"Row {idx}: Category ID {part_data.category_id} not found")
                failed += 1
                continue
            
            existing = db.query(Part).filter(
                Part.part_number == part_data.part_number
            ).first()
            if existing:
                errors.append(f"Row {idx}: Part number '{part_data.part_number}' already exists")
                failed += 1
                continue

            parts_to_insert.append(Part(
                **part_data.dict(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ))
            created += 1

        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
            failed += 1
    
    if parts_to_insert:
        db.add_all(parts_to_insert)
        db.commit()
    
    return {
        "total": len(parts_data),
        "created": created,
        "failed": failed,
        "errors": errors,
        "message": f"Created {created} parts, {failed} failed"
}
