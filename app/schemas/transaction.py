from datetime import datetime
from pydantic import BaseModel, ConfigDict
from enum import Enum

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class TransactionBase(BaseModel):
    amount: float
    category: str
    description: str | None = None
    type: TransactionType
    transaction_date: datetime | None = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    user_phone: str
    timestamp: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
