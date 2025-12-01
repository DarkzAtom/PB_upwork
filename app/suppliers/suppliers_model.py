from sqlalchemy import Column, Integer, String
from app.db_base import Base

class Supplier(Base):
    __tablename__ = 'suppliers'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
