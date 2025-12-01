from pydantic import BaseModel, Field
from typing import Optional

class BaseConfig:
    from_attributes = True

class WarehouseResponse(BaseModel):
    id: int
    supplier_id: int
    name: str
    country: str
    region: str
    shipping_zone_id: int
    default_lead_time_days: int

    class Config:
        from_attributes = True

class WarehouseCreate(BaseModel):
    supplier_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=1, max_length=200)
    region: str = Field(min_length=1, max_length=200)
    shipping_zone_id: int = Field(gt=0)
    default_lead_time_days: int = Field(ge=0)

class WarehouseUpdate(BaseModel):
    supplier_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    country: Optional[str] = Field(None, min_length=1, max_length=200)
    region: Optional[str] = Field(None, min_length=1, max_length=200)
    shipping_zone_id: Optional[int] = Field(None, gt=0)
    default_lead_time_days: Optional[int] = Field(None, ge=0)
