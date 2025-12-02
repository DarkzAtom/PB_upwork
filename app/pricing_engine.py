from sqlalchemy import exists, or_
from app.db_routers_connection import SessionLocal
from app.fx_rates.fx_rates_model import FxRate
from app.parts.parts_model import Part
from app.pricing_rules.pricing_rules_model import PricingRule
from app.supplier_price.supplier_price_model import SupplierPrice
from decimal import Decimal
from sqlalchemy.orm import Session

from app.warehouses.warehouses_model import Warehouse

class PricingEngine:
    def __init__(self, db: Session):
        self.db = db
    
    # Takes money value in currency and currency
    # Returns money value in PLN
    def convert_to_pln(self, price: Decimal, currency: str) -> Decimal:
        exchange_rate = self.db.query(FxRate).filter(FxRate.from_currency == currency, FxRate.to_currency == 'PLN').first()
        return price * exchange_rate.rate

    # Takes supplier_parts record
    # Return price with logistics in PLN
    def calculate_price_with_logistics(self, supplier_price: SupplierPrice) -> Decimal:
        base_price_pln = self.convert_to_pln(supplier_price.base_price, supplier_price.currency)
        # Logic for calculation of price with logistics
        # To be decided yet
        # ...
        price_with_logistics_pln = base_price_pln
        # ...
        # ...
        return price_with_logistics_pln

    # Takes parts record
    # Returns best supplier_price record
    def find_best_supplier_price(self, part: Part) -> SupplierPrice:
        eu_exists = self.db.query(
            exists()
            .where(SupplierPrice.part_id == part.id)
             .where(SupplierPrice.stock_status == 'Available')
             .where(SupplierPrice.warehouse_id == Warehouse.id)
            .where(Warehouse.region == 'EU')
        ).scalar()
        query = self.db.query(SupplierPrice).join(Warehouse).filter(SupplierPrice.part_id == part.id, SupplierPrice.stock_status == 'Available')
        if eu_exists:
            query = query.filter(Warehouse.region == 'EU')
        supplier_prices = query.all()
        return min(supplier_prices, key=lambda sp: (self.calculate_price_with_logistics(sp), sp.lead_time_days))

    # Takes supplier_prices record
    # Return pricing_rules record
    def get_pricing_rule(self, supplier_price: SupplierPrice) -> PricingRule:
        price_with_logistcs_pln = self.calculate_price_with_logistics(supplier_price)
        pricing_rule = self.db.query(PricingRule).order_by(PricingRule.priority.asc()).filter(
            or_(PricingRule.supplier_id == supplier_price.supplier_id, PricingRule.supplier_id.is_(None)),
            or_(PricingRule.brand_id == supplier_price.part.brand_id, PricingRule.brand_id.is_(None)),
            or_(PricingRule.category_id == supplier_price.part.category_id, PricingRule.category_id.is_(None)),
            PricingRule.price_min < price_with_logistcs_pln,
            PricingRule.price_max >= price_with_logistcs_pln,
            PricingRule.warehouse_region == supplier_price.warehouse.region,
            PricingRule.is_active).first()
        # If no rules applicable - use default rule
        return pricing_rule or PricingRule(
            rule_name='Default margin rule',
            margin_percent=Decimal('10'),
            fixed_markup=Decimal('10'),
            rounding_rule='Ceiling',
            priority=0,
            is_active=True)

    # Takes parts record
    # Returns final price in PLN 
    def calculate_final_price(self, part):
        supplier_price = self.find_best_supplier_price(part)
        pricing_rule = self.get_pricing_rule(supplier_price)
        return self.calculate_price_with_logistics(supplier_price) * (100% + pricing_rule.margin_percent) + pricing_rule.fixed_markup

if __name__ == '__main__':
    db = SessionLocal()
    eng = PricingEngine(db)

    print('convert_to_pln')
    value = eng.convert_to_pln(5, 'EUR')
    print(value)

    print('price_with_logistics')
    supplier_price = db.query(SupplierPrice).first()
    price_with_logistics = eng.calculate_price_with_logistics(supplier_price)
    print(price_with_logistics)

    print('find_best_supplier_price')
    part = db.query(Part).first()
    supplier_price = eng.find_best_supplier_price(part)
    print(supplier_price.id)

    print('get_pricing_rule')
    supplier_price = db.query(SupplierPrice).first()
    pricing_rule = eng.get_pricing_rule(supplier_price)
    print(pricing_rule.rule_name)
    print(pricing_rule.margin_percent)
    print(pricing_rule.fixed_markup)