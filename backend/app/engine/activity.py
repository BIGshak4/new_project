"""Solved-question calendar activity, independent of XP and correctness."""

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.engine.practice import assessed_by


def activity_summary(events: list[dict], timezone: str = "UTC", *, now: datetime | None = None) -> dict:
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        zone = UTC
    today = (now or datetime.now(UTC)).astimezone(zone).date()
    by_day: dict[date, set[str]] = defaultdict(set)
    for event in events:
        if event.get("status") != "done" or not event.get("band") or assessed_by(event.get("model")) != "model":
            continue
        if event.get("turn", 0) != 0 or set(event.get("flags") or []) & {"superseded", "content_review_pending"}:
            continue
        stamp = event.get("at")
        try:
            stamp = datetime.fromisoformat(stamp) if isinstance(stamp, str) else stamp
            if not isinstance(stamp, datetime):
                continue
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=UTC)
            day = stamp.astimezone(zone).date()
        except (ValueError, OverflowError):
            continue
        if day <= today and event.get("question"):
            by_day[day].add(str(event["question"]))
    cursor = today if today in by_day else today - timedelta(days=1)
    streak = 0
    while cursor in by_day:
        streak += 1
        cursor -= timedelta(days=1)
    days = sorted(by_day, reverse=True)
    return {"timezone": getattr(zone, "key", "UTC"), "today": today.isoformat(), "streak_days": streak,
            "today_count": len(by_day.get(today, set())),
            "last_solved_date": days[0].isoformat() if days else None,
            "days": [{"date": day.isoformat(), "questions": len(by_day[day])} for day in days[:14]]}
