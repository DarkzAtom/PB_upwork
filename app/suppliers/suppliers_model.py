from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db_base import Base

class Supplier(Base):
    __tablename__ = 'suppliers'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    warehouses = relationship('app.warehouses.warehouses_model.Warehouse', back_populates='supplier')
    supplier_prices = relationship('app.supplier_price.supplier_price_model.SupplierPrice', back_populates='supplier')
    pricing_rules = relationship('app.pricing_rules.pricing_rules_model.PricingRule', back_populates='supplier')
