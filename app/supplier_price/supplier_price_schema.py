from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class BaseConfig:
    from_attributes = True

class SupplierPriceResponse(BaseModel):
    id: int
    part_id: int
    supplier_id: int
    warehouse_id: int
    supplier_sku: str
    base_price: Decimal
    currency: str
    available_qty: int
    stock_status: str
    lead_time_days: int
    min_order_qty: Optional[int] = None
    pack_size: Optional[int] = None

    class Config:
        from_attributes = True

class SupplierPriceCreate(BaseModel):
    part_id: int = Field(gt=0)
    supplier_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    supplier_sku: str = Field(min_length=1)
    base_price: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    available_qty: int = Field(ge=0)
    stock_status: str = Field(min_length=1, max_length=100)
    lead_time_days: int = Field(ge=0)
    min_order_qty: Optional[int] = Field(None, ge=0)
    pack_size: Optional[int] = Field(None, ge=0)

class SupplierPriceUpdate(BaseModel):
    part_id: Optional[int] = Field(None, gt=0)
    supplier_id: Optional[int] = Field(None, gt=0)
    warehouse_id: Optional[int] = Field(None, gt=0)
    supplier_sku: Optional[str] = Field(None, min_length=1)
    base_price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    available_qty: Optional[int] = Field(None, ge=0)
    stock_status: Optional[str] = Field(None, min_length=1, max_length=100)
    lead_time_days: Optional[int] = Field(None, ge=0)
    min_order_qty: Optional[int] = Field(None, ge=0)
    pack_size: Optional[int] = Field(None, ge=0)
