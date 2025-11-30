from db_routers_connection import SessionLocal
from fx_rates.fx_rates_model import FxRate
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

    def get_pricing_rule(self, supplier_price):
        pass
    #     pricing_rules = db.get_pricing_rules(supplier_price.supplier_id, supplier_price.part.brand_id, supplier_price.part.category_id, supplier_price.price, supplier_price.warehouse_id)
    #     if pricing_rules == null
    #     return generic_pricing_rule
    #     pricing_rules.order_by(priority ASC)
    #     return pricing_rules[0]

    def convert_to_pln(self, price: Decimal, currency: str) -> Decimal:
        exchange_rate = self.db.query(FxRate).filter(FxRate.from_currency == currency, FxRate.to_currency == 'PLN').first()
        return price * exchange_rate.rate

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

if __name__ == "__main__":
    db = SessionLocal()
    eng = PricingEngine(db)

    value = eng.convert_to_pln(5, 'EUR')
    print(value)