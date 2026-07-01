from datetime import datetime, timezone


def parse_dt(value: datetime | str) -> datetime:
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def iso(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    return parse_dt(value).isoformat().replace("+00:00", "Z")
