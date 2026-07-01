from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.timeutils import parse_dt
from app.db.container import get_repositories


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
    }
