from datetime import date, timedelta
from app.database.models import ComplianceTask, FirmSettings


def get_firm_reminder_days():
    settings = FirmSettings.query.first()

    if not settings or not settings.reminder_days:
        return [15, 7, 3, 1]

    days = []

    for item in settings.reminder_days.split(","):
        item = item.strip()
        if item.isdigit():
            days.append(int(item))

    return days or [15, 7, 3, 1]


def get_due_today_tasks():
    today = date.today()

    return ComplianceTask.query.filter(
        ComplianceTask.due_date == today,
        ComplianceTask.status != "filed"
    ).all()


def get_upcoming_tasks_by_days(days):
    today = date.today()
    target_date = today + timedelta(days=days)

    return ComplianceTask.query.filter(
        ComplianceTask.due_date == target_date,
        ComplianceTask.status != "filed"
    ).order_by(ComplianceTask.due_date.asc()).all()


def get_overdue_tasks():
    today = date.today()

    return ComplianceTask.query.filter(
        ComplianceTask.due_date < today,
        ComplianceTask.status != "filed"
    ).order_by(ComplianceTask.due_date.asc()).all()


def get_reminder_summary():
    reminder_days = get_firm_reminder_days()

    upcoming_groups = []
    upcoming_total = 0

    for days in reminder_days:
        tasks = get_upcoming_tasks_by_days(days)
        upcoming_groups.append({
            "days": days,
            "tasks": tasks,
            "count": len(tasks)
        })
        upcoming_total += len(tasks)

    due_today = get_due_today_tasks()
    overdue = get_overdue_tasks()

    return {
        "reminder_days": reminder_days,
        "due_today": due_today,
        "overdue": overdue,
        "upcoming_groups": upcoming_groups,
        "due_today_count": len(due_today),
        "overdue_count": len(overdue),
        "upcoming_count": upcoming_total,
    }
