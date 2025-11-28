from sqlalchemy import ARRAY, Column, Integer, DateTime, Numeric, UniqueConstraint, func, String, ForeignKey, Double, Boolean
from sqlalchemy.dialects.postgresql import CHAR, JSONB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class ShippingZone(Base):
    __tablename__ = 'shipping_zones'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
