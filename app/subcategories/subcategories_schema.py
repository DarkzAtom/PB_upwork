from pydantic import BaseModel, Field
from typing import Optional

class BaseConfig:
    from_attributes = True

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
