from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class BaseConfig:
    from_attributes = True

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