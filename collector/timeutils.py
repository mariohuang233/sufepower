from datetime import datetime, timezone, timedelta

SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")

def now_shanghai() -> datetime:
    return datetime.now(SHANGHAI)

def slot_for(value: datetime | None = None) -> datetime:
    value = (value or now_shanghai()).astimezone(SHANGHAI)
    return value.replace(hour=(value.hour // 4) * 4, minute=0, second=0, microsecond=0)

def daily_slot_for(value: datetime | None = None) -> datetime:
    value = (value or now_shanghai()).astimezone(SHANGHAI)
    return value.replace(hour=23, minute=0, second=0, microsecond=0)

def iso(value: datetime) -> str:
    return value.astimezone(SHANGHAI).isoformat(timespec="seconds")
