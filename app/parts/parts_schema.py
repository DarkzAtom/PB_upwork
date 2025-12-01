from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal

class BaseConfig:
    from_attributes = True

class PartBasic(BaseModel):
    id: int
    brand_id: int
    part_number: str
    name: str
    images: Optional[List[str]] = None

    class Config:
        from_attributes = True

class PartDetail(BaseModel):
    id: int
    brand_id: int
    part_number: str
    normalized_part_number: str
    name: str
    description: str
    category_id: int
    subcategory_id: int
    images: Optional[List[str]] = None
    attributes: Optional[dict] = None
    vehicle_fitment: Optional[dict] = None

    class Config:
        from_attributes = True

class PartCreate(BaseModel):
    brand_id: int = Field(gt=0)
    part_number: str = Field(min_length=1, max_length=100)
    normalized_part_number: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1000)
    category_id: int = Field(gt=0)
    subcategory_id: int = Field(gt=0)
    images: Optional[List[str]] = Field(None)
    attributes: Optional[dict] = Field(None)
    vehicle_fitment: Optional[dict] = Field(None)
    

class PartUpdate(BaseModel):
    brand_id: Optional[int] = Field(None, gt=0)
    part_number: Optional[str] = None
    normalized_part_number: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = Field(None, gt=0)
    subcategory_id: Optional[int] = Field(None, gt=0)
    images: Optional[List[str]] = None
    attributes: Optional[dict] = None
    vehicle_fitment: Optional[dict] = None

class PartResponse(BaseModel):
    id: int
    brand_id: int
    part_number: str
    normalized_part_number: str
    name: str
    description: str
    category_id: int
    subcategory_id: int
    images: Optional[List[str]] = None
    attributes: Optional[dict] = None
    vehicle_fitment: Optional[dict] = None

    class Config:
        from_attributes = True

class PartAdmin(BaseModel):
    id: int
    part_number: str
    name: str
    brand: str
    supplier_id: int
    cost_price: Optional[Decimal] = None
    margin_percent: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    availability: Optional[str] = None

    class Config:
        from_attributes = True
