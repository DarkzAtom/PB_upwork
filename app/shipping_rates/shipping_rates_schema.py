from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class BaseConfig:
    from_attributes = True

class ShippingRateResponse(BaseModel):
    id: int
    shipping_zone_id: int
    warehouse_region: str
    weight_min: float
    weight_max: float
    price_pln: Decimal
    carrier: str
    service_level: str

    class Config:
        from_attributes = True

class ShippingRateCreate(BaseModel):
    shipping_zone_id: int = Field(gt=0)
    warehouse_region: str = Field(min_length=1, max_length=200)
    weight_min: float = Field(gt=0)
    weight_max: float = Field(gt=0)
    price_pln: Decimal = Field(gt=0)
    carrier: str = Field(min_length=1, max_length=200)
    service_level: str = Field(min_length=1, max_length=200)

class ShippingRateUpdate(BaseModel):
    shipping_zone_id: Optional[int] = Field(None, gt=0)
    warehouse_region: Optional[str] = Field(None, min_length=1, max_length=200)
    weight_min: Optional[float] = Field(None, gt=0)
    weight_max: Optional[float] = Field(None, gt=0)
    price_pln: Optional[Decimal] = Field(None, gt=0)
    carrier: Optional[str] = Field(None, min_length=1, max_length=200)
    service_level: Optional[str] = Field(None, min_length=1, max_length=200)
