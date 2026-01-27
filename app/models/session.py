from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.db.base import Base
import enum

class ConversationState(str, enum.Enum):
    """Conversation states for multi-turn dialogues."""
    IDLE = "IDLE"  # Ready for new commands
    AWAITING_CATEGORY = "AWAITING_CATEGORY"  # Waiting for transaction category
    AWAITING_AMOUNT = "AWAITING_AMOUNT"  # Waiting for transaction amount
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"  # Waiting for user confirmation

class Session(Base):
    """
    User conversation session for stateful interactions.
    
    Maintains conversation state and context between messages to enable
    multi-turn interactions like asking for missing transaction details.
    """
    __tablename__ = "sessions"

    user_phone = Column(String, ForeignKey("users.phone_number"), primary_key=True)  # User identifier
    state = Column(String, default=ConversationState.IDLE)  # Current conversation state
    context = Column(JSON, default={})  # Pending transaction data or conversation context
    last_interaction = Column(DateTime, default=datetime.utcnow)  # Last message timestamp
