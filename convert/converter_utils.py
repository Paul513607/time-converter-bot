import re 
from datetime import datetime, timedelta, timezone

TIME_24H = re.compile(r"\b([01]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])\b")  # HH:MM:SS
TIME_24H_SHORT = re.compile(r"\b([01]?[0-9]|2[0-3]):([0-5][0-9])\b")  # HH:MM
TIME_HOUR_ONLY = re.compile(r"\b([01]?[0-9]|2[0-3])\b")  # HH only
TIME_12H = re.compile(r"\b(1[0-2]|0?[1-9])(:[0-5][0-9])?\s?(AM|PM|am|pm)\b")  # HH AM/PM
RELATIVE_FUTURE = re.compile(r"\bin\s([1-9]|1[0-9]|2[0-3])\s?hours?\b")  # in X hours
RELATIVE_PAST = re.compile(r"\b([1-9]|1[0-9]|2[0-3])\s?hours?\sago\b")  # X hours ago

def parse_timezone(tz_string):
    pattern = r"UTC([+-]\d+)?"
    match = re.match(pattern, tz_string)
    
    if not match:
        raise ValueError(f"Invalid timezone format: {tz_string}")
    
    offset_str = match.group(1)
    if offset_str is None:
        return timezone.utc
    
    offset_hours = int(offset_str)
    offset_seconds = offset_hours * 3600
    return timezone(timedelta(seconds=offset_seconds))

def parse_message(message: str, tz_string: str) -> int:
    timezone = parse_timezone(tz_string)
    
    now = datetime.now(timezone)
    
    # Match absolute time (HH:MM:SS)
    if match := TIME_24H.search(message):
        hours, minutes, seconds = map(int, match.groups())
        target_time = now.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
        return int(target_time.timestamp())
    
    # Match absolute time (HH:MM)
    if match := TIME_24H_SHORT.search(message):
        hours, minutes = map(int, match.groups())
        target_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        return int(target_time.timestamp())
    
    # Match absolute time (HH only)
    if match := TIME_HOUR_ONLY.search(message):
        hours = int(match.group(1))
        target_time = now.replace(hour=hours, minute=0, second=0, microsecond=0)
        return int(target_time.timestamp())
    
    # Match 12-hour format
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
    
    # Match 'in X hours'
    if match := RELATIVE_FUTURE.search(message):
        hours = int(match.group(1))
        target_time = now + timedelta(hours=hours)
        return int(target_time.timestamp())
    
    # Match 'X hours ago'
    if match := RELATIVE_PAST.search(message):
        hours = int(match.group(1))
        target_time = now - timedelta(hours=hours)
        return int(target_time.timestamp())
    
    return -1   

def convert_to_tag(self, timestamp: int) -> str:
    return f"<t:{timestamp}:F>"

# check if the set timezone is a valid format (UTC+/-X)
def verify_timezone(self, timezone: str) -> bool:
    return re.match(r"UTC([+-]\d+)?", timezone) is not None
    