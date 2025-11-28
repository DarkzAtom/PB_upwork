from sqlalchemy import ARRAY, Column, Integer, DateTime, Numeric, UniqueConstraint, func, String, ForeignKey, Double, Boolean
from sqlalchemy.dialects.postgresql import CHAR, JSONB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

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
