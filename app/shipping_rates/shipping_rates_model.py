from sqlalchemy import ARRAY, Column, Integer, DateTime, Numeric, UniqueConstraint, func, String, ForeignKey, Double, Boolean
from sqlalchemy.dialects.postgresql import CHAR, JSONB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class ShippingRate(Base):
    __tablename__ = 'shipping_rates'

    id = Column(Integer, primary_key=True)
    shipping_zone_id = Column(Integer, ForeignKey('shipping_zones.id'), nullable=False)
    warehouse_region = Column(String, nullable=False)
    weight_min = Column(Double, nullable=False)
    weight_max = Column(Double, nullable=False)
    price_pln = Column(Numeric(19, 4), nullable=False)
    carrier = Column(String, nullable=False)
    service_level = Column(String, nullable=False)
