from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.db.base import Base

class User(Base):
    """
    User model for WhatsApp-based finance tracking system.
    
    Each user is identified by their WhatsApp phone number, which serves
    as the primary key. Users are automatically created when they first
    interact with the bot.
    """
    __tablename__ = "users"

    phone_number = Column(String, primary_key=True, index=True)  # WhatsApp phone number
    created_at = Column(DateTime, default=datetime.utcnow)  # When user first interacted
