from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    phone_number = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
