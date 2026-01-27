"""
Helper for formatting financial reports for WhatsApp.
"""
from datetime import datetime
from app.models.transaction import TransactionType

def format_currency(amount: float) -> str:
    """Format amount as currency string."""
    return f"{amount:,.2f}"

def format_report_header(title: str, start_date: datetime = None, end_date: datetime = None) -> str:
    """Format report header with date range."""
    header = f"📊 *{title}*"
    if start_date and end_date:
        header += f"\n🗓 {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
    return header

def create_bar_chart(data: dict, total: float, max_bars: int = 10) -> str:
    """Create a simple text-based bar chart."""
    if not data or total == 0:
        return ""
        
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:max_bars]
    max_val = sorted_items[0][1]
    
    chart_lines = []
    for label, value in sorted_items:
        # Calculate bar length (max 10 blocks)
        bar_len = int((value / max_val) * 10) if max_val > 0 else 0
        bar = "█" * bar_len
        percentage = (value / total) * 100
        chart_lines.append(f"{label[:12]:<12} {bar} {percentage:.0f}%")
        
    return "\n".join(chart_lines)

def format_financial_report(
    title: str,
    income: float,
    expenses: float,
    balance: float,
    category_breakdown: dict = None,
    start_date: datetime = None,
    end_date: datetime = None
) -> str:
    """
    Generate a formatted financial report string.
    """
    header = format_report_header(title, start_date, end_date)
    
    summary = (
        f"{header}\n\n"
        f"💰 Income:   {format_currency(income)}\n"
        f"💸 Expenses: {format_currency(expenses)}\n"
        f"🏦 Balance:  {format_currency(balance)}\n"
    )
    
    if category_breakdown:
        chart = create_bar_chart(category_breakdown, expenses)
        summary += f"\n*Spending by Category:*\n```\n{chart}\n```"
        
    return summary
