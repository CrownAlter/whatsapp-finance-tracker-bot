from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base

class TransactionType(str, enum.Enum):
    """Enumeration of transaction types."""
    INCOME = "income"
    EXPENSE = "expense"

class Transaction(Base):
    """
    Financial transaction record for tracking income and expenses.
    
    Supports both one-time and recurring transactions with automatic
    timestamp tracking and user association.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)  # Primary key
    user_phone = Column(String, ForeignKey("users.phone_number"))  # User identifier
    amount = Column(Float, nullable=False)  # Transaction amount (positive value)
    category = Column(String, nullable=False)  # Transaction category (food, rent, etc.)
    type = Column(Enum(TransactionType), nullable=False)  # INCOME or EXPENSE
    timestamp = Column(DateTime, default=datetime.utcnow)  # When record was created
    transaction_date = Column(DateTime, default=datetime.utcnow)  # When transaction occurred
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)  # Last modification
    description = Column(String, nullable=True)  # Optional description/notes

    user = relationship("User", backref="transactions")
