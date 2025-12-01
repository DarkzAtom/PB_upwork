from sqlalchemy import Column, Integer, String
from app.db_base import Base

class ShippingZone(Base):
    __tablename__ = 'shipping_zones'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
