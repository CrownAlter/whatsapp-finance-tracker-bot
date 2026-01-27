"""
Help messages and command examples for the Finance Tracker Bot.
"""

WELCOME_MESSAGE = """👋 *Welcome to Finance Tracker Bot!*

I'll help you track your income and expenses via WhatsApp.

*Quick Start:*
• Log expense: `Spent 100 on food`
• Log income: `Income 5000 salary`
• View report: `Show report`

Type `/help` for more commands!
"""

HELP_MESSAGE = """📖 *Finance Tracker Bot - Commands*

*💸 Logging Expenses:*
• `Spent 100 on food`
• `Paid 2500 for rent`
• `Bought groceries for 1500`
• `Spent 800 transport yesterday`

*💰 Logging Income:*
• `Income 5000 salary`
• `Received 1000 bonus`
• `Salary 120000`

*📊 Reports:*
• `Show report` - All-time summary
• `Weekly report` - Last 7 days
• `Monthly report` - Last 30 days
• `This week` - Current week
• `This month` - Current month

*📝 Transaction History:*
• `Show history` - Last 10 transactions
• `Show last 20` - Last 20 transactions

*✏️ Managing Transactions:*
• `Delete last` - Delete last transaction
• `Edit last category to food` - Change category

*📂 Categories:*
• `Show categories` - List all categories

*❓ Help:*
• `/help` or `help` - Show this message

*Examples:*
✅ Spent 2500 on food yesterday
✅ Income 120000 salary
✅ Paid 800 for transport
✅ Show weekly report
"""

CATEGORY_LIST_MESSAGE = """📂 *Available Categories*

*Expenses:*
• Food & Dining: food, groceries, dining, restaurants
• Transport: transport, uber, taxi, fuel
• Housing: rent, utilities, electricity, water
• Shopping: shopping, clothes, electronics
• Health: health, medical, gym, pharmacy
• Entertainment: entertainment, movies, subscriptions
• Education: education, school, books
• Travel: travel, vacation, hotel
• Other: insurance, personal, gifts, charity

*Income:*
• salary, bonus, freelance, investment, gift

💡 *Tip:* I'll auto-correct similar spellings!
"""

ERROR_MESSAGES = {
    "unknown_command": """❓ I didn't understand that.

Try:
• `Spent 100 on food`
• `Income 5000 salary`
• `Show report`
• Type `/help` for all commands""",
    
    "invalid_amount": """❌ Invalid amount.

Please use numbers like:
• 100
• 1000.50
• 2.5k (for 2500)""",
    
    "missing_category": """❓ What category is this for?

Examples: food, transport, rent, utilities

Or type `/help` for all categories""",
    
    "invalid_category": """❓ Category not recognized.

Did you mean: {suggestion}?

Type `show categories` to see all options.""",
    
    "no_transactions": """📭 No transactions found.

Start tracking by sending:
`Spent 100 on food`""",
    
    "delete_failed": """❌ Couldn't delete transaction.

Make sure you have transactions to delete.
Try `show history` first.""",
}


def get_error_message(error_type: str, **kwargs) -> str:
    """
    Get a formatted error message.
    
    Args:
        error_type: Type of error
        **kwargs: Additional parameters for formatting
        
    Returns:
        Formatted error message
    """
    message = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["unknown_command"])
    return message.format(**kwargs)
