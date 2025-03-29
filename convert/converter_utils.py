import re 
from datetime import datetime, timedelta, timezone
import pytz

# HH:MM (24-hour format, 0-23h)
TIME_24H_SHORT = re.compile(r"\b([01]?[0-9]|2[0-3]):([0-5][0-9])\b")  
# "at HH" only (0-23h)
TIME_HOUR_ONLY = re.compile(r"\bat\s([01]?[0-9]|2[0-3])\b", re.IGNORECASE)
# HH:MM AM/PM or HH AM/PM (12-hour format, case-insensitive)
TIME_12H = re.compile(r"\b(1[0-2]|0?[1-9])(:[0-5][0-9])?\s?(AM|PM|am|pm)\b")  
# Relative time: "in X hours", "in X minutes", "in Xh", "in X min"
RELATIVE_FUTURE = re.compile(r"\bin\s(\d{1,2})\s?(h|hours?|m|min|minutes?)\b", re.IGNORECASE)
# Relative time: "X hours ago", "X minutes ago", "Xh ago", "X min ago"
RELATIVE_PAST = re.compile(r"\b(\d{1,2})\s?(h|hours?|m|min|minutes?)\sago\b", re.IGNORECASE)

def parse_message(message: str, tz_string: str) -> int:
    timezone = pytz.timezone(tz_string)
    now = datetime.now(timezone)

    # Match 'in X hours/minutes', 'in Xh', 'in X min'
    if match := RELATIVE_FUTURE.search(message):
        amount, unit = match.groups()
        amount = int(amount)
        if unit.startswith("h"):  # hours
            target_time = now + timedelta(hours=amount)
        else:  # minutes
            target_time = now + timedelta(minutes=amount)
        return int(target_time.timestamp())

    # Match 'X hours/minutes ago', 'Xh ago', 'X min ago'
    if match := RELATIVE_PAST.search(message):
        amount, unit = match.groups()
        amount = int(amount)
        if unit.startswith("h"):  # hours
            target_time = now - timedelta(hours=amount)
        else:  # minutes
            target_time = now - timedelta(minutes=amount)
        return int(target_time.timestamp())
    
    # Match 12-hour format (HH AM/PM or HH:MM AM/PM)
    if match := TIME_12H.search(message):
        hours, minutes, period = match.groups()
        hours = int(hours)
        minutes = int(minutes[1:]) if minutes else 0
        if period.lower() == "pm" and hours != 12:
            hours += 12
        if period.lower() == "am" and hours == 12:
            hours = 0
        target_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        return int(target_time.timestamp())
    
    # Match absolute time (HH:MM in 24-hour format)
    if match := TIME_24H_SHORT.search(message):
        hours, minutes = map(int, match.groups())
        target_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        return int(target_time.timestamp())

    # Match absolute time (HH only)
    if match := TIME_HOUR_ONLY.search(message):
        hours = int(match.group(1))
        target_time = now.replace(hour=hours, minute=0, second=0, microsecond=0)
        return int(target_time.timestamp())

    return -1 

def convert_to_tag(timestamp: int) -> str:
    return f"<t:{timestamp}:F>"

def verify_timezone(timezone: str) -> bool:
    return timezone in pytz.all_timezones_set