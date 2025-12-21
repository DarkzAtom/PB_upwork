from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class BaseConfig:
    from_attributes = True

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
