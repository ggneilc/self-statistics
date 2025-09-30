from datetime import datetime
from zoneinfo import ZoneInfo
from core.models import Day


def get_or_create_today(user):
    """Returns today's Day object for the given user, creating it if needed."""
    tz = ZoneInfo(user.profile.timezone)
    local_today = datetime.now(tz).date()
    day, _ = Day.objects.get_or_create(user=user, date=local_today)
    return day


def get_or_create_day(user, selected_date):
    day, _ = Day.objects.get_or_create(user=user, date=selected_date)
    return day
