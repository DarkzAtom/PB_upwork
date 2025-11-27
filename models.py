from sqlalchemy import ARRAY, Column, Integer, DateTime, Numeric, UniqueConstraint, func, String, ForeignKey, Double, Boolean
from sqlalchemy.dialects.postgresql import CHAR, JSONB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Part(Base):
    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True)
    # supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    # supplier_part_id = Column(String, nullable=False)
    brand_id = Column(Integer, ForeignKey('brands.id'), nullable=False)
    part_number = Column(String, nullable=False)
    normalized_part_number = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    subcategory_id = Column(Integer, ForeignKey('subcategories.id'), nullable=False)
    images = Column(ARRAY(String), nullable=True)
    attributes = Column(JSONB, nullable=True)
    vehicle_fitment = Column(JSONB, nullable=True)


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


class FxRate(Base):
    __tablename__ = 'fx_rates'

    id = Column(Integer, primary_key=True)
    from_currency = Column(CHAR(3), nullable=False)
    to_currency = Column(CHAR(3), nullable=False, default='PLN')
    rate = Column(Numeric(15, 6), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=func.now())

    UniqueConstraint(from_currency, to_currency)


class Supplier(Base):
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class Warehouse(Base):
    __tablename__ = 'warehouses'

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    region = Column(String, nullable=False)
    shipping_zone_id = Column(Integer, ForeignKey('shipping_zones.id'), nullable=False)
    default_lead_time_days = Column(Integer, nullable=False)


# class Inventory(Base):
#     __tablename__ = 'inventories'

#     id = Column(Integer, primary_key=True)
#     warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
#     part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
#     available_qty = Column(Integer, nullable=False)
#     stock_status = Column(String, nullable=False)
#     updated_at = Column(DateTime, nullable=False, default=func.now())


class PricingRule(Base):
    __tablename__ = 'pricing_rules'

    id = Column(Integer, primary_key=True)
    rule_name = Column(String, nullable=False, unique=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    brand_id = Column(Integer, ForeignKey('brands.id'), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    price_min = Column(Numeric(19, 4), nullable=False)
    price_max = Column(Numeric(19, 4), nullable=False)
    warehouse_region = Column(String, nullable=False)
    margin_percent = Column(Numeric(5, 2), nullable=False)
    fixed_markup = Column(Numeric(19, 4), nullable=False)
    rounding_rule = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False)


class ShippingZone(Base):
    __tablename__ = 'shipping_zones'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


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


class Brand(Base):
    __tablename__ = 'brands'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class Subcategory(Base):
    __tablename__ = 'subcategories'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    name = Column(String, nullable=False)
