from sqlalchemy import ARRAY, Column, Integer, DateTime, Numeric, UniqueConstraint, func, String, ForeignKey, Double, Boolean
from sqlalchemy.dialects.postgresql import CHAR, JSONB
from db_base import Base

class FxRate(Base):
    __tablename__ = 'fx_rates'

    id = Column(Integer, primary_key=True)
    from_currency = Column(CHAR(3), nullable=False)
    to_currency = Column(CHAR(3), nullable=False, default='PLN')
    rate = Column(Numeric(15, 6), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=func.now())

    UniqueConstraint(from_currency, to_currency)
