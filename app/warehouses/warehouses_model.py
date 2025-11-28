from sqlalchemy import ARRAY, Column, Integer, DateTime, Numeric, UniqueConstraint, func, String, ForeignKey, Double, Boolean
from sqlalchemy.dialects.postgresql import CHAR, JSONB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Warehouse(Base):
    __tablename__ = 'warehouses'

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    region = Column(String, nullable=False)
    shipping_zone_id = Column(Integer, ForeignKey('shipping_zones.id'), nullable=False)
    default_lead_time_days = Column(Integer, nullable=False)
