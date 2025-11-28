from sqlalchemy import ARRAY, Column, Integer, DateTime, Numeric, UniqueConstraint, func, String, ForeignKey, Double, Boolean
from sqlalchemy.dialects.postgresql import CHAR, JSONB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class SupplierPrice(Base):
    __tablename__ = 'supplier_prices'

    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    supplier_sku = Column(String, nullable=False)
    base_price = Column(Numeric(19, 4), nullable=False)
    currency = Column(CHAR(3), nullable=False)
    available_qty = Column(Integer, nullable=False)
    stock_status = Column(String, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    min_order_qty = Column(Integer, nullable=True)
    pack_size = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=func.now())
