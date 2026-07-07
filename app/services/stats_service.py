from collections import Counter, defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.exceptions import ValidationAppError
from app.core.timeutils import parse_dt
from app.db.container import get_repositories

# World-stage thresholds (mirrors world_service.STAGES / api-doc.md business rules).
_STAGE_THRESHOLDS = [(100, 5), (50, 4), (30, 3), (15, 2), (5, 1), (0, 0)]


def _world_stage_for(books_completed: int) -> int:
    for threshold, stage in _STAGE_THRESHOLDS:
        if books_completed >= threshold:
            return stage
    return 0


def _active_days(sessions: list[dict], tz: ZoneInfo) -> set:
    return {parse_dt(s["date"]).astimezone(tz).date() for s in sessions}


def _streak(days: set, today) -> tuple[int, int]:
    if not days:
        return 0, 0

    current = 0
    cursor = today if today in days else today - timedelta(days=1)
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)

    longest = 0
    run = 0
    prev = None
    for d in sorted(days):
        run = run + 1 if prev is not None and (d - prev).days == 1 else 1
        longest = max(longest, run)
        prev = d
    return current, longest


def get_dashboard(user_id: str, tz_name: str = "UTC") -> dict:
    repos = get_repositories()
    user = repos.users.get_by_id(user_id)
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")

    sessions = repos.sessions.list_all_by_user(user_id)
    days = _active_days(sessions, tz)
    today = datetime.now(tz).date()
    current_days, longest_days = _streak(days, today)

    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    weekly = sum(1 for d in days if d >= week_start)
    monthly = sum(1 for d in days if d >= month_start)
    yearly = sum(1 for d in days if d >= year_start)
    active_today = today in days

    _, currently_reading_count = repos.books.list_by_user(
        user_id, "currently_reading", None, None, "-updated_at", 1, 1
    )

    per_day_pages: dict = defaultdict(int)
    for s in sessions:
        d = parse_dt(s["date"]).astimezone(tz).date()
        if week_start <= d <= today:
            per_day_pages[d] += s["pages_read"]

    week_days = [week_start + timedelta(days=i) for i in range(7)]
    weekly_chart = []
    this_week_pages = 0
    for d in week_days:
        pages = per_day_pages.get(d, 0)
        this_week_pages += pages
        weekly_chart.append({"label": d.strftime("%a"), "date": d.isoformat(), "pages": pages})

    # Bounded to the last 100 finished books; sufficient for a "this week" count
    # without a dedicated aggregate query.
    finished_books, _ = repos.books.list_by_user(
        user_id, "already_read", None, None, "-finished_at", 1, 100
    )
    this_week_books = sum(
        1
        for b in finished_books
        if b.get("finished_at") and parse_dt(b["finished_at"]).astimezone(tz).date() >= week_start
    )
    books_this_year = sum(
        1
        for b in finished_books
        if b.get("finished_at") and parse_dt(b["finished_at"]).astimezone(tz).date() >= year_start
    )

    daily_goal_pages = user.get("daily_goal_pages", 10)
    pages_today = per_day_pages.get(today, 0)

    return {
        "display_name": user["display_name"],
        "books_completed": user["books_completed"],
        "currently_reading_count": currently_reading_count,
        "points": user["points"],
        "world_stage": user["world_stage"],
        "streaks": {
            "current_days": current_days,
            "longest_days": longest_days,
            "weekly": weekly,
            "monthly": monthly,
            "yearly": yearly,
            "active_today": active_today,
        },
        "this_week": {
            "pages": this_week_pages,
            "books_finished": this_week_books,
            "days_active": weekly,
        },
        "weekly_chart": weekly_chart,
        "daily_goal_pages": daily_goal_pages,
        "pages_today": pages_today,
        "daily_goal_met": pages_today >= daily_goal_pages,
        "books_this_year": books_this_year,
    }


def _first_of_next_month(d):
    return d.replace(year=d.year + 1, month=1, day=1) if d.month == 12 else d.replace(
        month=d.month + 1, day=1
    )


def _longest_streak(days: set) -> int:
    longest = 0
    run = 0
    prev = None
    for d in sorted(days):
        run = run + 1 if prev is not None and (d - prev).days == 1 else 1
        longest = max(longest, run)
        prev = d
    return longest


def get_wrapped(user_id: str, month: str | None, tz_name: str = "UTC") -> dict:
    repos = get_repositories()
    user = repos.users.get_by_id(user_id)
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")

    today = datetime.now(tz).date()
    current_month = today.replace(day=1)
    created_month = parse_dt(user["created_at"]).astimezone(tz).date().replace(day=1)

    if month is None:
        month_start = current_month
    else:
        try:
            month_start = datetime.strptime(month, "%Y-%m").date().replace(day=1)
        except ValueError as exc:
            raise ValidationAppError(
                "month must be in YYYY-MM format", {"errors": {"month": "invalid_format"}}
            ) from exc
        if month_start < created_month or month_start > current_month:
            raise ValidationAppError(
                "month is out of range", {"errors": {"month": "out_of_range"}}
            )

    next_month_start = _first_of_next_month(month_start)

    # Reading sessions within the month (user-local day).
    sessions = repos.sessions.list_all_by_user(user_id)
    pages_read = 0
    reading_days: set = set()
    for s in sessions:
        d = parse_dt(s["date"]).astimezone(tz).date()
        if month_start <= d < next_month_start:
            pages_read += s["pages_read"]
            reading_days.add(d)

    # Finished books — bounded fetch is enough for this project's scale.
    finished_books, _ = repos.books.list_by_user(
        user_id, "already_read", None, None, "-finished_at", 1, 1000
    )
    finished_dates = [
        (parse_dt(b["finished_at"]).astimezone(tz).date(), b.get("genre"))
        for b in finished_books
        if b.get("finished_at")
    ]
    in_month = [(d, g) for d, g in finished_dates if month_start <= d < next_month_start]

    genres = Counter(g for _, g in in_month if g)
    top_genre = genres.most_common(1)[0][0] if genres else None

    books_before = sum(1 for d, _ in finished_dates if d < month_start)
    books_after = sum(1 for d, _ in finished_dates if d < next_month_start)
    stage_delta = _world_stage_for(books_after) - _world_stage_for(books_before)

    return {
        "month": month_start.strftime("%Y-%m"),
        "books_finished": len(in_month),
        "pages_read": pages_read,
        "reading_days": len(reading_days),
        "longest_streak": _longest_streak(reading_days),
        "top_genre": top_genre,
        "world_stage": _world_stage_for(books_after),
        "stage_delta": stage_delta,
    }
