from sqlalchemy import ARRAY, Column, Integer, DateTime, Numeric, UniqueConstraint, func, String, ForeignKey, Double, Boolean
from sqlalchemy.dialects.postgresql import CHAR, JSONB
from db_base import Base

class ShippingZone(Base):
    __tablename__ = 'shipping_zones'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
