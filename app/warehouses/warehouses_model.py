from sqlalchemy import Column, Integer, String, ForeignKey
from app.db_base import Base

class Warehouse(Base):
    __tablename__ = 'warehouses'

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    region = Column(String, nullable=False)
    shipping_zone_id = Column(Integer, ForeignKey('shipping_zones.id'), nullable=False)
    default_lead_time_days = Column(Integer, nullable=False)
