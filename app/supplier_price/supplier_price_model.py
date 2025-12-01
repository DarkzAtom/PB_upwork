from sqlalchemy import Column, Integer, DateTime, Numeric, func, String, ForeignKey
from sqlalchemy.dialects.postgresql import CHAR
from sqlalchemy.orm import relationship
from app.db_base import Base

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

    part = relationship('app.parts.parts_model.Part', back_populates='supplier_prices')
    supplier = relationship('app.suppliers.suppliers_model.Supplier', back_populates='supplier_prices')
    warehouse = relationship('app.warehouses.warehouses_model.Warehouse', back_populates='supplier_prices')
