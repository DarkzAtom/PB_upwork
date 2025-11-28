from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class BaseConfig:
    from_attributes = True

# FX Rates

class FxRateResponse(BaseModel):
    id: int
    from_currency: str
    to_currency: str
    rate: Decimal
    updated_at: datetime

    class Config:
        from_attributes = True

class FxRateCreate(BaseModel):
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3, default='PLN')
    rate: Decimal = Field(gt=0)

class FxRateUpdate(BaseModel):
    from_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    to_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    rate: Optional[Decimal] = Field(None, gt=0)
    updated_at: Optional[datetime] = Field(None)

# Shipping Zones

class ShippingZoneResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ShippingZoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

class ShippingZoneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)

# Shipping Rates

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

# Suppliers

class SupplierResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)

# Brands

class BrandResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class BrandCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    
class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)

# Categories

class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)

# Subcategories

class SubcategoryResponse(BaseModel):
    id: int
    parent_id: int
    name: str

    class Config:
        from_attributes = True

class SubcategoryCreate(BaseModel):
    parent_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)

class SubcategoryUpdate(BaseModel):
    parent_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, min_length=1, max_length=200)

# Parts

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

# Warehouses

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

# Supplier Prices

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

# Pricing Rules

class PricingRuleResponse(BaseModel):
    id: int
    rule_name: str
    supplier_id: Optional[int]
    brand_id: Optional[int]
    category_id: Optional[int]
    price_min: Decimal
    price_max: Decimal
    warehouse_region: str
    margin_percent: Decimal
    fixed_markup: Decimal
    rounding_rule: str
    priority: int
    is_active: bool

    class Config:
        from_attributes = True

class PricingRuleCreate(BaseModel):
    rule_name: str = Field(min_length=1, max_length=200, alias="name")
    supplier_id: Optional[int] = Field(None, gt=0)
    brand_id: Optional[int] = Field(None, gt=0)
    category_id: Optional[int] = Field(None, gt=0)
    price_min: Decimal = Field(gt=0)
    price_max: Decimal = Field(gt=0)
    warehouse_region: str = Field(min_length=1, max_length=200)
    margin_percent: Decimal = Field(gt=0)
    fixed_markup: Decimal = Field(gt=0)
    rounding_rule: str = Field(min_length=1, max_length=100)
    priority: int = Field(gt=0)
    is_active: bool = True
    
    class Config:
        from_attributes = True
        populate_by_name = True

class PricingRuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, min_length=1, max_length=200, alias="name")
    supplier_id: Optional[int] = Field(None, gt=0)
    brand_id: Optional[int] = Field(None, gt=0)
    category_id: Optional[int] = Field(None, gt=0)
    price_min: Optional[Decimal] = Field(None, gt=0)
    price_max: Optional[Decimal] = Field(None, gt=0)
    warehouse_region: Optional[str] = Field(None, min_length=1, max_length=200)
    margin_percent: Optional[Decimal] = Field(None, gt=0)
    fixed_markup: Optional[Decimal] = Field(None, gt=0)
    rounding_rule: Optional[str] = Field(None, min_length=1, max_length=100)
    priority: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True

# Inventory

# class InventoryResponse(BaseModel):
#     id: int
#     part_id: int
#     warehouse_id: int
#     available_qty: int
#     stock_status: str
#     updated_at: datetime

# class InventoryCreate(BaseModel):
#     part_id: int = Field(gt=0)
#     warehouse_id: int = Field(gt=0)
#     available_qty: int = Field(ge=0)
#     stock_status: str = Field(min_length=1, max_length=100)
#     updated_at: Optional[datetime] = Field(None)


# class InventoryUpdate(BaseModel):
#     part_id: Optional[int] = Field(None, gt=0)
#     warehouse_id: Optional[int] = Field(None, gt=0)
#     available_qty: Optional[int] = Field(None, ge=0)
#     stock_status: Optional[str] = Field(None, min_length=1, max_length=100)
#     updated_at: Optional[datetime] = Field(None)

