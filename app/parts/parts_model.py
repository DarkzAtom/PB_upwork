from sqlalchemy import ARRAY, Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db_base import Base

class Part(Base):
    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True)
    # supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    # supplier_part_id = Column(String, nullable=False)
    brand_id = Column(Integer, ForeignKey('brands.id'), nullable=False)
    part_number = Column(String, nullable=False)
    normalized_part_number = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    subcategory_id = Column(Integer, ForeignKey('subcategories.id'), nullable=False)
    images = Column(ARRAY(String), nullable=True)
    attributes = Column(JSONB, nullable=True)
    vehicle_fitment = Column(JSONB, nullable=True)

    brand = relationship('app.brands.brands_model.Brand', back_populates='parts')
    category = relationship('app.categories.categories_model.Category', back_populates='parts')
    subcategory = relationship('app.subcategories.subcategories_model.Subcategory', back_populates='parts')

    supplier_prices = relationship('app.supplier_price.supplier_price_model.SupplierPrice', back_populates='part')
