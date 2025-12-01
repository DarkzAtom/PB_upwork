from sqlalchemy import Column, Integer, String, ForeignKey
from app.db_base import Base

class Subcategory(Base):
    __tablename__ = 'subcategories'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    name = Column(String, nullable=False)
