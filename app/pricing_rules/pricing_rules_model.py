from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db_base import Base

class PricingRule(Base):
    __tablename__ = 'pricing_rules'

    id = Column(Integer, primary_key=True)
    rule_name = Column(String, nullable=False, unique=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    brand_id = Column(Integer, ForeignKey('brands.id'), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    price_min = Column(Numeric(19, 4), nullable=False)
    price_max = Column(Numeric(19, 4), nullable=False)
    warehouse_region = Column(String, nullable=False)
    margin_percent = Column(Numeric(5, 2), nullable=False)
    fixed_markup = Column(Numeric(19, 4), nullable=False)
    rounding_rule = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False)

    supplier = relationship('app.suppliers.suppliers_model.Supplier', back_populates='pricing_rules')
    brand = relationship('app.brands.brands_model.Brand', back_populates='pricing_rules')
    category = relationship('app.categories.categories_model.Category', back_populates='pricing_rules')
