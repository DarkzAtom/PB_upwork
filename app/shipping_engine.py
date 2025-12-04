from typing import TypedDict
from sqlalchemy.orm import Session
from app.db_routers_connection import SessionLocal
from app.parts.parts_model import Part
from app.shipping_rates.shipping_rates_model import ShippingRate
from app.shipping_zones.shipping_zones_model import ShippingZone
from app.supplier_price.supplier_price_model import SupplierPrice
from decimal import Decimal
from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy import and_

from app.warehouses.warehouses_model import Warehouse

class PriceQuantity(TypedDict):
    supplier_price: SupplierPrice
    quantity: int

class ShippingCostDate(TypedDict):
    cost: Decimal
    delivery_date: date

class ShippingEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def get_availability_status(self, part: Part) -> str:
        statuses = self.db.query(SupplierPrice.stock_status).where(SupplierPrice.part_id == part.id).distinct().all()
        statuses = [row[0] for row in statuses]
        
        if 'Available' in statuses:
            return 'Available'
        elif 'Low stock' in statuses:
            return 'Low stock'
        elif 'Unavailable' in statuses:
            return 'Unavailable'
        else:
            return 'Unavailable'
    
    def country_to_shipping_zone(self, country: str) -> ShippingZone:
        # To be implemented
        return self.db.query(ShippingZone).where(ShippingZone.name == 'EU').first()

    def calculate_shipping_time_and_cost_cart(self, prices: list[PriceQuantity], country: str) -> ShippingCostDate:
        shipping_zone = self.country_to_shipping_zone(country)
        
        warehouse_groups = defaultdict(list)
        for price_qty in prices:
            supplier_price = price_qty['supplier_price']
            quantity = price_qty['quantity']
            warehouse_id = supplier_price.warehouse_id
            warehouse_groups[warehouse_id].append({
                'supplier_price': supplier_price,
                'quantity': quantity
            })
        
        total_shipping_cost = Decimal('0')
        max_delivery_days = 0
        
        for warehouse_id, items in warehouse_groups.items():
            warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            
            # To be implemented, currently it just use 5 as a weight for every part
            # What source of weight data should be used?
            total_weight = sum(item['quantity'] * 5 for item in items)
            
            shipping_rate = db.query(ShippingRate).filter(
                ShippingRate.shipping_zone_id == shipping_zone.id,
                ShippingRate.warehouse_region == warehouse.region,
                ShippingRate.weight_min <= total_weight,
                ShippingRate.weight_max >= total_weight
            ).first()
            
            total_shipping_cost += Decimal(str(shipping_rate.price_pln))

            max_lead_time = max(item['supplier_price'].lead_time_days for item in items)
            
            # To be implemented
            # What source of carrier delivery time should be used?
            warehouse_delivery_days = max_lead_time #+ carrier delivery time
            
            max_delivery_days = max(max_delivery_days, warehouse_delivery_days)
        
        return ShippingCostDate(
            cost=total_shipping_cost,
            delivery_date=date.today() + timedelta(days=max_delivery_days)
        )

if __name__ == '__main__':
    db = SessionLocal()
    eng = ShippingEngine(db)

    part = db.query(Part).first()
    status = eng.get_availability_status(part)
    print(status)

    supplier_prices = db.query(SupplierPrice).all()
    price_quantity = []
    for price in supplier_prices:
        price_quantity.append(PriceQuantity(supplier_price=price, quantity=1))

    eng.calculate_shipping_time_and_cost_cart(price_quantity, 'Poland')