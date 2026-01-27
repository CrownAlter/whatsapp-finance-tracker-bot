from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.services.report_formatter import format_financial_report
from typing import List, Optional, Tuple, Dict
from sqlalchemy import func, desc
from datetime import datetime, timedelta

class FinanceEngine:
    """
    Core financial calculations and transaction management engine.
    
    Handles transaction processing, report generation, and financial
    analytics including period-based summaries and category breakdowns.
    """
    
    # Default limits and periods
    DEFAULT_TRANSACTION_LIMIT = 10  # Number of transactions to return by default
    DAILY_PERIOD_DAYS = 1
    WEEKLY_PERIOD_DAYS = 7
    MONTHLY_PERIOD_DAYS = 30
    
    def process_transaction(self, db: Session, user_phone: str, data: dict):
        """
        Create and store a new transaction record.
        
        Args:
            db: Database session
            user_phone: User's WhatsApp phone number
            data: Transaction data (amount, category, type, description, date)
            
        Returns:
            Created Transaction object
            
        Raises:
            ValueError: If required transaction data is missing
        """
        # Ensure user exists (create if not exists)
        user = db.query(User).filter(User.phone_number == user_phone).first()
        if not user:
            user = User(phone_number=user_phone)
            db.add(user)
            db.commit()
            
        transaction = Transaction(
            user_phone=user_phone,
            amount=data['amount'],
            category=data['category'],
            type=data['type'],
            description=data.get('description'),
            transaction_date=data.get('date') or datetime.utcnow(),
            timestamp=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    def generate_report(self, db: Session, user_phone: str, period: str = "all") -> str:
        """
        Generates a financial report.
        """
        query = db.query(Transaction).filter(Transaction.user_phone == user_phone)
        
        start_date = None
        end_date = datetime.utcnow()
        title = "Financial Report"
        
        if period == "weekly" or period == "week":
            start_date = end_date - timedelta(days=7)
            title = "Weekly Report (Last 7 Days)"
        elif period == "monthly" or period == "month":
            start_date = end_date - timedelta(days=30)
            title = "Monthly Report (Last 30 Days)"
        elif period == "daily" or period == "day":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            title = "Daily Report"
            
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
            
        transactions = query.all()
        
        if not transactions:
            return f"📭 No transactions found for {title}."
            
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        total_expense = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        balance = total_income - total_expense
        
        # Category breakdown for expenses
        categories = {}
        for t in transactions:
            if t.type == TransactionType.EXPENSE:
                categories[t.category] = categories.get(t.category, 0) + t.amount
                
        return format_financial_report(
            title, total_income, total_expense, balance, categories, start_date, end_date
        )

    def get_transaction_history(self, db: Session, user_phone: str, limit: int = 10) -> str:
        """Get formatted transaction history."""
        transactions = db.query(Transaction)\
            .filter(Transaction.user_phone == user_phone)\
            .order_by(desc(Transaction.transaction_date))\
            .limit(limit)\
            .all()
            
        if not transactions:
            return "📭 No transactions found."
            
        lines = ["📜 *Recent Transactions*"]
        for t in transactions:
            icon = "🔴" if t.type == TransactionType.EXPENSE else "🟢"
            date_str = t.transaction_date.strftime("%d/%m")
            lines.append(f"{icon} {date_str}: {t.amount:,.0f} ({t.category})")
            
        return "\n".join(lines)
        
    def delete_last_transaction(self, db: Session, user_phone: str) -> str:
        """Delete the most recent transaction."""
        last_t = db.query(Transaction)\
            .filter(Transaction.user_phone == user_phone)\
            .order_by(desc(Transaction.timestamp))\
            .first()
            
        if not last_t:
            return "❌ No transaction to delete."
            
        amount = last_t.amount
        category = last_t.category
        db.delete(last_t)
        db.commit()
        
        return f"🗑️ Deleted: {amount} for {category}"

finance_engine = FinanceEngine()
