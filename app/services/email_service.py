from app.database.models import FirmSettings
from app.services.reminder_service import get_reminder_summary


def get_firm_settings():
    return FirmSettings.query.first()


def build_email_subject(task, reminder_label):
    return f"Reminder: {task.form_name} {reminder_label}"


def build_email_body(task, reminder_label):
    firm = get_firm_settings()
    firm_name = firm.firm_name if firm else "Khans & Co"
    firm_email = firm.email if firm and firm.email else ""

    client = task.client
    period = f"{task.period_month or ''} {task.period_year or ''}".strip()
    due_date = task.due_date.strftime("%d-%m-%Y") if task.due_date else "-"

    return f"""Dear {client.client_name},

This is a reminder from {firm_name}.

Your {task.form_name} ({task.compliance_type}) for {period} is {reminder_label}.
Due Date: {due_date}

Please share required details/documents at the earliest.

Regards,
{firm_name}
{("Email: " + firm_email) if firm_email else ""}
"""


def build_email_queue():
    summary = get_reminder_summary()
    queue = []

    def add_task(task, reminder_label, priority):
        client = task.client
        queue.append({
            "task_id": task.id,
            "client_id": client.id,
            "client_name": client.client_name,
            "business_name": client.business_name,
            "email": client.email or "",
            "compliance_type": task.compliance_type,
            "form_name": task.form_name,
            "period": f"{task.period_month or ''} {task.period_year or ''}".strip(),
            "due_date": task.due_date.strftime("%d-%m-%Y") if task.due_date else "-",
            "status": task.status,
            "reminder_label": reminder_label,
            "priority": priority,
            "subject": build_email_subject(task, reminder_label),
            "body": build_email_body(task, reminder_label)
        })

    for task in summary["overdue"]:
        add_task(task, "overdue", "danger")

    for task in summary["due_today"]:
        add_task(task, "due today", "warning")

    for group in summary["upcoming_groups"]:
        for task in group["tasks"]:
            add_task(task, f"due in {group['days']} day{'s' if group['days'] != 1 else ''}", "info")

    return queue
