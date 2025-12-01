from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, Double
from app.db_base import Base
from sqlalchemy.orm import relationship

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

    shipping_zone = relationship('app.shipping_zones.shipping_zones_model.ShippingZone', back_populates='shipping_rates')
