import re
from datetime import datetime, date, timedelta
from dateutil import parser as dtparser
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

def _split_nums(date_str: str) -> list[int]:
    normalized = date_str.replace(".", "/").replace("-", "/")
    normalized = normalized.replace(",", "/").replace(" ", "/")
    parts = [p.strip() for p in normalized.split("/") if p.strip()]
    nums = []
    for p in parts:
        digits = re.sub(r'\D', '', p)
        if digits:
            try:
                nums.append(int(digits))
            except ValueError:
                pass
    return nums

def parse_date_any(date_text: str, fuzzy: bool = True) -> str:
    if not date_text or not date_text.strip():
        raise ValueError("Date cannot be empty")
    
    s = date_text.strip().lower()
    today = date.today()
    
    if s in ("today", "сьогодні", "сегодня"):
        return today.strftime("%Y-%m-%d")
    if s in ("yesterday", "вчора", "вчера"):
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    if s in ("tomorrow", "завтра"):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    relative_match = re.match(
        r'(\d+)\s*(day|days|week|weeks|month|months|днів|дня|день|тиждень|тижнів|місяць|місяців)\s*(ago|тому|назад)',
        s
    )
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)
        if 'day' in unit or 'день' in unit or 'дн' in unit:
            delta = timedelta(days=amount)
        elif 'week' in unit or 'тиждень' in unit or 'тижн' in unit:
            delta = timedelta(weeks=amount)
        elif 'month' in unit or 'місяц' in unit:
            delta = timedelta(days=amount * 30)
        else:
            delta = timedelta(days=0)
        return (today - delta).strftime("%Y-%m-%d")
    
    nums = _split_nums(s)
    yearfirst = False
    dayfirst = True
    
    if len(s) >= 4 and s[:4].isdigit():
        yearfirst = True
        dayfirst = False
    elif len(nums) >= 2:
        a, b = nums[0], nums[1]
        if a > 12 and b <= 12:
            dayfirst = True
        elif a <= 12 and b > 12:
            dayfirst = False
        else:
            dayfirst = True
    
    try:
        dt = dtparser.parse(s, dayfirst=dayfirst, yearfirst=yearfirst, fuzzy=fuzzy)
        if dt.year < 1900 or dt.year > 2100:
            raise ValueError(f"Year {dt.year} is out of reasonable range")
        if dt.date() > today:
            logger.warning(f"Parsed date {dt.date()} is in the future")
        result = dt.strftime("%Y-%m-%d")
        logger.debug(f"Parsed '{date_text}' as {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to parse date '{date_text}': {e}")
        raise ValueError(
            f"❌ Invalid date format: {date_text}\n\n"
            "Supported formats:\n"
            "• DD.MM.YYYY (01.02.2020)\n"
            "• YYYY-MM-DD (2020-02-01)\n"
            "• 'today', 'yesterday'\n"
            "• '2 days ago'"
        )
