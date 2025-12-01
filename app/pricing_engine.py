from sqlalchemy import or_
from app.db_routers_connection import SessionLocal
from app.fx_rates.fx_rates_model import FxRate
from app.pricing_rules.pricing_rules_model import PricingRule
from app.supplier_price.supplier_price_model import SupplierPrice
from decimal import Decimal
from sqlalchemy.orm import Session

class PricingEngine:
    def __init__(self, db: Session):
        self.db = db

    def find_best_supplier_price(self, part):
        pass
    #     supplier_prices = db.get_supplier_prices(part, status=AVAILABLE)
    #     if supplier_prices.containts(warehouse=EU)
    #     supplier_prices = supplier_prices.filter(warehouse=EU)
    #     supplier_prices.order_by(cost_with_logistics ASC, lead_time_days ASC)
    #     return supplier_price[0]

    def convert_to_pln(self, price: Decimal, currency: str) -> Decimal:
        exchange_rate = self.db.query(FxRate).filter(FxRate.from_currency == currency, FxRate.to_currency == 'PLN').first()
        return price * exchange_rate.rate

    def get_pricing_rule(self, supplier_price: SupplierPrice) -> PricingRule:
        price_pln = self.convert_to_pln(supplier_price.base_price, supplier_price.currency)
        pricing_rule = self.db.query(PricingRule).order_by(PricingRule.priority.asc()).filter(
            or_(PricingRule.supplier_id == supplier_price.supplier_id, PricingRule.supplier_id.is_(None)),
            or_(PricingRule.brand_id == supplier_price.part.brand_id, PricingRule.brand_id.is_(None)),
            or_(PricingRule.category_id == supplier_price.part.category_id, PricingRule.category_id.is_(None)),
            PricingRule.price_min < price_pln,
            PricingRule.price_max >= price_pln,
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

    def calculate_price_with_logistics(self, supplier_price):
        pass
    #     return base_price

    def calculate_final_price(self, part):
        pass
    #     supplier_price = find_best_supplier_price(part)
    #     price_with_logitsics = calculate_price_with_logistics(supplier_price)
    #     pricing_rule = get_pricing_rule(supplier_price)
    #     final_price = price_with_logistics * (100% + pricing_rule.margin_percent) + pricing_rule.fixed_markup
    #     return final_price

if __name__ == '__main__':
    db = SessionLocal()
    eng = PricingEngine(db)

    value = eng.convert_to_pln(5, 'EUR')
    print(value)

    supplier_price = db.query(SupplierPrice).first()
    print(supplier_price.currency)
    print(supplier_price.base_price)
    print(supplier_price.warehouse.region)

    pricing_rule = eng.get_pricing_rule(supplier_price)
    print(pricing_rule.rule_name)
    print(pricing_rule.margin_percent)
    print(pricing_rule.fixed_markup)