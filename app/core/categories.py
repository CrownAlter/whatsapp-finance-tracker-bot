"""
Category definitions and management for the Finance Tracker Bot.
"""
from typing import List, Optional, Dict
from fuzzywuzzy import process

# Predefined expense categories
EXPENSE_CATEGORIES = [
    "food",
    "groceries",
    "transport",
    "transportation",
    "utilities",
    "rent",
    "housing",
    "entertainment",
    "shopping",
    "health",
    "healthcare",
    "education",
    "travel",
    "dining",
    "restaurants",
    "subscriptions",
    "insurance",
    "personal",
    "gifts",
    "charity",
    "savings",
    "investments",
    "other"
]

# Income categories
INCOME_CATEGORIES = [
    "salary",
    "income",
    "bonus",
    "freelance",
    "investment",
    "gift",
    "refund",
    "other"
]

# Category aliases - map common variations to standard categories
CATEGORY_ALIASES: Dict[str, str] = {
    # Food related
    "food": "food",
    "groceries": "groceries",
    "grocery": "groceries",
    "dining": "dining",
    "restaurant": "restaurants",
    "restaurants": "restaurants",
    "eating": "food",
    "lunch": "food",
    "dinner": "food",
    "breakfast": "food",
    
    # Transport
    "transport": "transport",
    "transportation": "transport",
    "uber": "transport",
    "taxi": "transport",
    "bus": "transport",
    "train": "transport",
    "fuel": "transport",
    "gas": "transport",
    "parking": "transport",
    
    # Housing
    "rent": "rent",
    "housing": "housing",
    "mortgage": "housing",
    "utilities": "utilities",
    "electricity": "utilities",
    "water": "utilities",
    "internet": "utilities",
    "phone": "utilities",
    
    # Entertainment
    "entertainment": "entertainment",
    "movies": "entertainment",
    "games": "entertainment",
    "music": "entertainment",
    "streaming": "subscriptions",
    "netflix": "subscriptions",
    "spotify": "subscriptions",
    
    # Shopping
    "shopping": "shopping",
    "clothes": "shopping",
    "clothing": "shopping",
    "electronics": "shopping",
    
    # Health
    "health": "health",
    "healthcare": "health",
    "medical": "health",
    "doctor": "health",
    "pharmacy": "health",
    "medicine": "health",
    "gym": "health",
    "fitness": "health",
    
    # Other
    "education": "education",
    "school": "education",
    "books": "education",
    "travel": "travel",
    "vacation": "travel",
    "hotel": "travel",
    "insurance": "insurance",
    "personal": "personal",
    "gifts": "gifts",
    "charity": "charity",
    "donation": "charity",
    "savings": "savings",
    "investment": "investments",
    "investments": "investments",
    "other": "other",
    "miscellaneous": "other",
    "misc": "other",
}


def normalize_category(category: str) -> str:
    """
    Normalize a category name using aliases.
    
    Args:
        category: Raw category name from user input
        
    Returns:
        Normalized category name
    """
    category_lower = category.lower().strip()
    return CATEGORY_ALIASES.get(category_lower, category_lower)


def validate_category(category: str, transaction_type: str = "expense") -> tuple[bool, str]:
    """
    Validate if a category is valid and return normalized version.
    
    Args:
        category: Category to validate
        transaction_type: "expense" or "income"
        
    Returns:
        Tuple of (is_valid, normalized_category)
    """
    normalized = normalize_category(category)
    
    valid_categories = EXPENSE_CATEGORIES if transaction_type == "expense" else INCOME_CATEGORIES
    
    if normalized in valid_categories:
        return True, normalized
    
    return False, normalized


def suggest_category(category: str, transaction_type: str = "expense", threshold: int = 70) -> Optional[str]:
    """
    Suggest a category based on fuzzy matching.
    
    Args:
        category: User's category input
        transaction_type: "expense" or "income"
        threshold: Minimum similarity score (0-100)
        
    Returns:
        Suggested category or None
    """
    valid_categories = EXPENSE_CATEGORIES if transaction_type == "expense" else INCOME_CATEGORIES
    
    # Try fuzzy matching
    result = process.extractOne(category.lower(), valid_categories)
    
    if result and result[1] >= threshold:
        return result[0]
    
    return None


def get_all_categories(transaction_type: str = "expense") -> List[str]:
    """
    Get all valid categories for a transaction type.
    
    Args:
        transaction_type: "expense" or "income"
        
    Returns:
        List of valid categories
    """
    return EXPENSE_CATEGORIES if transaction_type == "expense" else INCOME_CATEGORIES
