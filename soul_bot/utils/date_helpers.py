"""
Date/Time utility functions
"""
from datetime import datetime


def add_months(now: datetime, months: int) -> datetime:
    """
    Add months to a datetime object
    
    Args:
        now: Current datetime
        months: Number of months to add
        
    Returns:
        New datetime with added months
    """
    if now.month + months > 12:
        return now.replace(year=now.year + 1, month=(now.month + months) - 12)
    
    return now.replace(month=now.month + months)

