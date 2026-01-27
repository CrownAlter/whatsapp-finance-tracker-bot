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
    """
    Manages multi-turn conversations with users for financial tracking.
    
    Handles state transitions, context preservation, and guides users
    through complex operations like categorization or error recovery.
    
    States:
        IDLE: Ready for new commands
        AWAITING_CATEGORY: Waiting for user to provide transaction category
        AWAITING_AMOUNT: Waiting for transaction amount
        AWAITING_CONFIRMATION: Waiting for user confirmation
    """
    
    def get_session(self, db: DbSession, user_phone: str) -> Session:
        """
        Get or create a conversation session for the user.
        
        Args:
            db: Database session
            user_phone: User's WhatsApp phone number
            
        Returns:
            Session object for conversation state management
        """
        session = db.query(Session).filter(Session.user_phone == user_phone).first()
        if not session:
            # Create user if doesn't exist
            user = db.query(User).filter(User.phone_number == user_phone).first()
            if not user:
                user = User(phone_number=user_phone)
                db.add(user)
                db.commit()
            
            # Create new conversation session
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
            return "❌ Cancelled. What can I help you with?"
        
        if intent == "help":
            self.update_state(db, session, ConversationState.IDLE, {})
            return get_error_message("help")
        
        # 2. State-specific handling
        if state == ConversationState.AWAITING_CATEGORY:
            return self.handle_awaiting_category(db, session, message)
        
        if state == ConversationState.AWAITING_AMOUNT:
            return self.handle_awaiting_amount(db, session, message)
        
        if state == ConversationState.AWAITING_CONFIRMATION:
            return self.handle_awaiting_confirmation(db, session, message)
            
        # 3. Intent-based handling when IDLE
        if intent == "log_transaction":
            # Validate transaction data
            if not data.get("amount"):
                self.update_state(db, session, ConversationState.AWAITING_AMOUNT, {"type": data.get("type", "expense")})
                return "❓ How much was the transaction?"
                
            if not data.get("category"):
                self.update_state(db, session, ConversationState.AWAITING_CATEGORY, data)
                return "❓ What category is this for? Examples: food, transport, rent, bills"
            
            # All data present, create transaction
            return self.create_transaction_with_context(db, user_phone, data)
        
        # 4. Other intents (reports, history) are handled directly
        if intent == "get_report":
            period = data.get("period", "all")
            report = finance_engine.generate_report(db, user_phone, period)
            self.update_state(db, session, ConversationState.IDLE, {})
            return report
        
        if intent == "get_history":
            history = finance_engine.get_transaction_history(db, user_phone)
            self.update_state(db, session, ConversationState.IDLE, {})
            return history
            
        if intent == "delete_transaction":
            target = data.get("target", "last")
            success = finance_engine.delete_transaction(db, user_phone, target)
            self.update_state(db, session, ConversationState.IDLE, {})
            if success:
                return "✅ Transaction deleted."
            return "❌ Could not delete transaction."
            
        if intent == "list_categories":
            from app.core.categories import get_categories_for_type
            cats = get_categories_for_type("expense") # Could make this dynamic
            self.update_state(db, session, ConversationState.IDLE, {})
            return f"📝 Available categories: {', '.join(cats)}"
              
        return get_error_message("unknown_command")

    def handle_awaiting_category(self, db: DbSession, session: Session, message: str) -> str:
        """
        Process user input when waiting for transaction category.
        
        Validates the provided category, handles suggestions for similar categories,
        and either completes the transaction or prompts for better input.
        
        Args:
            db: Database session
            session: User's conversation session with pending transaction data
            message: User's category input
            
        Returns:
            Response message confirming transaction or requesting clarification
        """
        context_data = session.context
        candidate = message.strip().split()[0]
        
        # Validate against known categories for transaction type
        is_valid, normalized = validate_category(candidate, context_data.get("type", "expense"))
        
        if is_valid:
            # Complete pending transaction with valid category
            context_data['category'] = normalized
            
            try:
                # Note: JSON serialization may lose datetime objects
                # For production, use proper JSON encoder or separate storage
                transaction = finance_engine.process_transaction(db, session.user_phone, context_data)
                self.update_state(db, session, ConversationState.IDLE, {})
                return f"✅ Recorded: {transaction.type.value} of {transaction.amount} for {transaction.category}."
            except Exception as e:
                self.update_state(db, session, ConversationState.IDLE, {})
                return f"❌ Error saving transaction: {str(e)}"
        else:
            # Try to suggest similar categories based on fuzzy matching
            suggested = suggest_category(candidate, context_data.get("type", "expense"))
            if suggested:
                return get_error_message("invalid_category", suggestion=suggested)
            return "❓ Valid category required. Try 'food', 'transport', 'bills' etc."

    def handle_awaiting_amount(self, db: DbSession, session: Session, message: str) -> str:
        """Handle input when waiting for an amount."""
        # Simple amount extraction - should be enhanced
        try:
            # Look for numbers in the message
            import re
            amount_match = re.search(r'(\d+(\.\d+)?)', message)
            if not amount_match:
                return "❌ I couldn't find a valid amount. Please enter just a number like '100' or '99.50'"
            
            amount = float(amount_match.group(1))
            context_data = session.context
            context_data['amount'] = amount
            
            # Now check if we have category
            if not context_data.get("category"):
                self.update_state(db, session, ConversationState.AWAITING_CATEGORY, context_data)
                return "❓ What category is this for?"
            
            # Complete the transaction
            return self.create_transaction_with_context(db, session.user_phone, context_data)
            
        except ValueError:
            return "❌ Invalid amount format. Please enter just a number like '100' or '99.50'"

    def handle_awaiting_confirmation(self, db: DbSession, session: Session, message: str) -> str:
        """Handle confirmation responses."""
        response = message.lower().strip()
        
        if response in ["yes", "y", "confirm", "ok", "save"]:
            # Confirm and create transaction
            context_data = session.context
            return self.create_transaction_with_context(db, session.user_phone, context_data)
        
        elif response in ["no", "n", "cancel", "discard"]:
            # Cancel the pending transaction
            self.update_state(db, session, ConversationState.IDLE, {})
            return "❌ Transaction cancelled."
        
        else:
            # Ask for clear confirmation
            return "❓ Please confirm with 'yes' or cancel with 'no'"

    def create_transaction_with_context(self, db: DbSession, user_phone: str, data: dict) -> str:
        """Helper to create transaction and reset conversation state."""
        try:
            transaction = finance_engine.process_transaction(db, user_phone, data)
            # Reset state after successful creation
            session = self.get_session(db, user_phone)
            self.update_state(db, session, ConversationState.IDLE, {})
            return f"✅ Recorded: {transaction.type.value} of {transaction.amount} for {transaction.category}."
        except Exception as e:
            # Reset state on error
            session = self.get_session(db, user_phone)
            self.update_state(db, session, ConversationState.IDLE, {})
            return f"❌ Error: {str(e)}"

conversation_manager = ConversationManager()