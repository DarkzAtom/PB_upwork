from sqlalchemy.orm import Session
from app.db_routers_connection import SessionLocal
from app.parts.parts_model import Part
from app.supplier_price.supplier_price_model import SupplierPrice

class ShippingEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def get_availability_status(self, part: Part) -> str:
        statuses = self.db.query(SupplierPrice.stock_status).distinct().all()
        statuses = [row[0] for row in statuses]
        
        if 'Available' in statuses:
            return 'Available'
        elif 'Low stock' in statuses:
            return 'Low stock'
        elif 'Unavailable' in statuses:
            return 'Unavailable'
        else:
            return 'Unavailable'

if __name__ == '__main__':
    db = SessionLocal()
    eng = ShippingEngine(db)

    part = db.query(Part).first()
    status = eng.get_availability_status(part)
    print(status)