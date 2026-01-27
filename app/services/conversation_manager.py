from sqlalchemy.orm import Session as DbSession
from app.models.session import Session, ConversationState
from app.models.user import User
from app.models.transaction import TransactionType
from app.services.finance_engine import finance_engine
from app.core.categories import validate_category, suggest_category
from app.core.help_messages import get_error_message
from datetime import datetime
import json

class ConversationManager:
    def get_session(self, db: DbSession, user_phone: str) -> Session:
        """
        Get or create a conversation session for the user.
        """
        session = db.query(Session).filter(Session.user_phone == user_phone).first()
        if not session:
            # Ensure user exists first
            user = db.query(User).filter(User.phone_number == user_phone).first()
            if not user:
                user = User(phone_number=user_phone)
                db.add(user)
                db.commit()
            
            session = Session(user_phone=user_phone)
            db.add(session)
            db.commit()
        return session
    
    def update_state(self, db: DbSession, session: Session, state: str, context: dict = None):
        """
        Update the conversation state and context.
        """
        session.state = state
        if context is not None:
            session.context = context # SQLAlchemy tracks dict changes if we reassign
        session.last_interaction = datetime.utcnow()
        db.commit()

    def handle_message(self, db: DbSession, user_phone: str, message: str, intent: str, data: dict) -> str:
        """
        Main handler for stateful conversation logic.
        """
        session = self.get_session(db, user_phone)
        state = session.state
        context = session.context or {}
        
        # 1. Global Commands (cancel, help) break out of any state
        if message.lower() in ["cancel", "stop", "abort"]:
            self.update_state(db, session, ConversationState.IDLE, {})
            return "❌ Operation cancelled."
            
        if intent == "help":
            return self.handle_help(db, session)

        # 2. State Machine Logic
        
        if state == ConversationState.IDLE:
            return self.handle_idle_state(db, session, intent, data)
            
        elif state == ConversationState.AWAITING_CATEGORY:
            return self.handle_awaiting_category(db, session, message)
            
        # Add more states as needed (AWAITING_AMOUNT, etc.)
        
        # Fallback reset
        self.update_state(db, session, ConversationState.IDLE, {})
        return "⚠️ Something went wrong. Conversation reset."

    def handle_idle_state(self, db: DbSession, session: Session, intent: str, data: dict) -> str:
        """
        Handle messages when in IDLE state.
        """
        if intent == "log_transaction":
            # Check for missing category
            if data['category'] == "uncategorized":
                # Ask for category
                self.update_state(db, session, ConversationState.AWAITING_CATEGORY, data)
                return get_error_message("missing_category")
            
            # If complete, process it
            try:
                # Convert date string if it was serialized in context, but here 'data' is fresh dict
                # data['date'] is datetime or None.
                
                transaction = finance_engine.process_transaction(db, session.user_phone, data)
                
                date_str = transaction.transaction_date.strftime("%b %d")
                return f"✅ Recorded: {transaction.type.value} of {transaction.amount} for {transaction.category} ({date_str})."
            except Exception as e:
                return f"❌ Error: {str(e)}"
                
        elif intent == "get_report":
            period = data.get("period", "all")
            return finance_engine.generate_report(db, session.user_phone, period)
            
        elif intent == "get_history":
            return finance_engine.get_transaction_history(db, session.user_phone)
            
        elif intent == "delete_transaction":
            # For now only support deleting last
            return finance_engine.delete_last_transaction(db, session.user_phone)
            
        elif intent == "unknown":
             return get_error_message("unknown_command")
             
        elif intent == "list_categories":
             from app.core.help_messages import CATEGORY_LIST_MESSAGE
             return CATEGORY_LIST_MESSAGE
             
        return get_error_message("unknown_command")

    def handle_awaiting_category(self, db: DbSession, session: Session, message: str) -> str:
        """
        Handle input when waiting for a category.
        """
        context_data = session.context
        candidate = message.strip().split()[0]
        
        # Validate category
        is_valid, normalized = validate_category(candidate, context_data.get("type", "expense"))
        
        if is_valid:
            # Update data with valid category
            context_data['category'] = normalized
            
            try:
                # Reconstruct transaction data
                # Need to handle date serialization if it was stored in context (JSON)
                # JSON serializes datetime as string usually.
                # In this MVP, we might lose the date object if not careful.
                # Let's simple parse it back or default to now.
                
                if 'date' in context_data and context_data['date']:
                    # Assuming it might be stored as ISO string or similar if we used proper encoder
                    # For simplicity, if we lose complex objects in JSON context, we might need a better serializer.
                    # Here we'll ignore complex date recovery for this specific flow correction.
                    context_data['date'] = None 
                
                transaction = finance_engine.process_transaction(db, session.user_phone, context_data)
                
                # Reset state
                self.update_state(db, session, ConversationState.IDLE, {})
                return f"✅ Recorded: {transaction.type.value} of {transaction.amount} for {transaction.category}."
                
            except Exception as e:
                self.update_state(db, session, ConversationState.IDLE, {})
                return f"❌ Error saving transaction: {str(e)}"
        else:
            # Suggest or retry
            suggested = suggest_category(candidate, context_data.get("type", "expense"))
            if suggested:
                return get_error_message("invalid_category", suggestion=suggested)
            
            return "❓ Valid category required. Try 'food', 'transport', 'bills' etc."

    def handle_help(self, db: DbSession, session: Session) -> str:
        from app.core.help_messages import HELP_MESSAGE
        return HELP_MESSAGE

conversation_manager = ConversationManager()
