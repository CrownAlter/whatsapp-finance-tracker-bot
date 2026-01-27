import re
from typing import Dict, Any, Tuple
from app.schemas.transaction import TransactionType
from app.services.date_parser import parse_date
from app.core.categories import normalize_category, suggest_category, validate_category
from datetime import datetime

class MessageProcessor:
    def __init__(self):
        # Regex patterns
        # Amount: Matches integers, decimals (10.50), and suffix k/m (2.5k)
        self.amount_pattern = r"(?P<amount>\d+(\.\d+)?)\s*(?P<multiplier>[km])?"
        
        # Expense: "spent 100 on food", "bought items for 200", "paid 500 rent"
        self.expense_pattern = re.compile(
            rf"(spent|paid|bought)\s+{self.amount_pattern}\s+(on|for)?\s*(?P<rest>.*)", 
            re.IGNORECASE
        )
        
        # Income: "income 5000 salary", "received 500 bonus", "salary 2000"
        self.income_pattern = re.compile(
            rf"(income|salary|received)\s+{self.amount_pattern}\s*(?P<rest>.*)", 
            re.IGNORECASE
        )
        
        # Commands
        self.report_pattern = re.compile(r"(show|get|view)?\s*(daily|weekly|monthly)?\s*(report|summary|stats)", re.IGNORECASE)
        self.history_pattern = re.compile(r"(show|get|view)?\s*(transaction)?\s*history", re.IGNORECASE)
        self.help_pattern = re.compile(r"/?help|commands|usage", re.IGNORECASE)
        self.categories_pattern = re.compile(r"(show|get|view|list)\s*categories", re.IGNORECASE)
        self.delete_pattern = re.compile(r"delete\s*(last|transaction)?\s*(\d*)", re.IGNORECASE)

    def _parse_amount(self, amount_str: str, multiplier: str) -> float:
        """Helper to parse amount with multipliers (k, m)."""
        value = float(amount_str)
        if multiplier:
            if multiplier.lower() == 'k':
                value *= 1000
            elif multiplier.lower() == 'm':
                value *= 1000000
        return value

    def parse_message(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parses the message and returns an intent and extracted data.
        """
        message = message.strip()
        
        # 1. Help & Info Commands
        if self.help_pattern.match(message):
            return "help", {}
            
        if self.categories_pattern.search(message):
            return "list_categories", {}

        # 2. History & Transaction Management
        if self.report_pattern.search(message):
            match = self.report_pattern.search(message)
            period = match.group(2) if match.group(2) else "all"
            return "get_report", {"period": period.lower()}
            
        if self.history_pattern.search(message):
            return "get_history", {}
            
        delete_match = self.delete_pattern.match(message)
        if delete_match:
            target = delete_match.group(2)
            return "delete_transaction", {"target": target if target else "last"}

        # 3. Transaction Logging
        
        # Check for expense
        expense_match = self.expense_pattern.search(message)
        if expense_match:
            try:
                amount = self._parse_amount(expense_match.group("amount"), expense_match.group("multiplier"))
                rest = expense_match.group("rest").strip()
                
                # Extract date from the "rest" part
                date_obj = parse_date(rest)
                if date_obj:
                    # Remove the date string from description to find category
                    # This is a simplification; for better results, we'd remove the specific substring matched by dateparser
                    # But dateparser doesn't easily return the matched span. 
                    # Assuming date is often at the end.
                    pass 
                
                # If date found, we use it. If not, default to current time (handled in DB/schema usually, 
                # but here we pass it if found)
                
                # Category extraction: simple heuristic + validation
                # Split remainder by words, check if any is a valid category
                # Fallback: Treat the whole 'rest' as category if short, or 'uncategorized'
                
                category = "uncategorized"
                description = None
                
                # Heuristic: First word after amount/preposition is candidate for category
                if rest:
                    # Remove date-like words from rest to find category
                    # For now, let's just pick the first word as category candidate
                    words = rest.split()
                    candidate = words[0]
                    
                    is_valid, normalized = validate_category(candidate, "expense")
                    if is_valid:
                        category = normalized
                        # Description might be the rest
                        description = " ".join(words[1:]) if len(words) > 1 else None
                    else:
                        # Try suggestion
                        suggested = suggest_category(candidate, "expense")
                        if suggested:
                            category = suggested
                            description = " ".join(words[1:]) if len(words) > 1 else None
                        else:
                            # If no match, check common things or just use text as description
                            description = rest
                            
                return "log_transaction", {
                    "amount": amount,
                    "category": category,
                    "type": TransactionType.EXPENSE,
                    "date": date_obj,
                    "description": description
                }
            except ValueError:
                pass # Float conversion error
            
        # Check for income
        income_match = self.income_pattern.search(message)
        if income_match:
            try:
                amount = self._parse_amount(income_match.group("amount"), income_match.group("multiplier"))
                rest = income_match.group("rest").strip()
                
                date_obj = parse_date(rest)
                category = "income" # Default
                
                # Check for specific income category (salary, bonus)
                if rest:
                    words = rest.split()
                    candidate = words[0]
                    is_valid, normalized = validate_category(candidate, "income")
                    if is_valid:
                        category = normalized
                
                return "log_transaction", {
                    "amount": amount,
                    "category": category,
                    "type": TransactionType.INCOME,
                    "date": date_obj
                }
            except ValueError:
                pass

        return "unknown", {}

message_processor = MessageProcessor()
