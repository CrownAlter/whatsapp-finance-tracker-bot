from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.db.base import Base
import enum

class ConversationState(str, enum.Enum):
    IDLE = "IDLE"
    AWAITING_CATEGORY = "AWAITING_CATEGORY"
    AWAITING_AMOUNT = "AWAITING_AMOUNT" 
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"

class Session(Base):
    __tablename__ = "sessions"

    user_phone = Column(String, ForeignKey("users.phone_number"), primary_key=True)
    state = Column(String, default=ConversationState.IDLE)
    context = Column(JSON, default={})
    last_interaction = Column(DateTime, default=datetime.utcnow)
