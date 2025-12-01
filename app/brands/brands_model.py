from sqlalchemy import Column, Integer, String
from app.db_base import Base
from sqlalchemy.orm import relationship

class Brand(Base):
    __tablename__ = 'brands'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    parts = relationship('app.parts.parts_model.Part', back_populates='brand')
    pricing_rules = relationship('app.pricing_rules.pricing_rules_model.PricingRule', back_populates='brand')
