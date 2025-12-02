from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal


class CartItemInput(BaseModel):
    part_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class CartPriceRequest(BaseModel):
    items: List[CartItemInput] = Field(min_length=1)
    delivery_country: str = Field(min_length=2, max_length=100)


class CartItemOutput(BaseModel):
    part_id: int
    part_number: str
    name: str
    quantity: int
    unit_price_pln: Decimal


class CartPriceResponse(BaseModel):
    items: List[CartItemOutput]
    subtotal_pln: Decimal
    shipping_cost_pln: Decimal
    total_pln: Decimal
    estimated_delivery_days: str
