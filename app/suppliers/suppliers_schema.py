from pydantic import BaseModel, Field
from typing import Optional

class BaseConfig:
    from_attributes = True

class SupplierResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
