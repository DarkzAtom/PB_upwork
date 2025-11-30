from sqlalchemy.orm import sessionmaker
from db_connection import engine

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()