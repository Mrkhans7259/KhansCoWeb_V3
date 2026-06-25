from app.database.models import FirmSettings
from app.services.reminder_service import get_reminder_summary


def get_firm_settings():
    return FirmSettings.query.first()


def build_whatsapp_message(task, reminder_label):
    firm = get_firm_settings()
    firm_name = firm.firm_name if firm else "Khans & Co"
    firm_mobile = firm.mobile if firm and firm.mobile else ""

    client = task.client
    period = f"{task.period_month or ''} {task.period_year or ''}".strip()
    due_date = task.due_date.strftime("%d-%m-%Y") if task.due_date else "-"

    return (
        f"Dear {client.client_name},\\n\\n"
        f"This is a reminder from {firm_name}.\\n\\n"
        f"Your {task.form_name} ({task.compliance_type}) for {period} is {reminder_label}.\\n"
        f"Due Date: {due_date}\\n\\n"
        f"Please share required details/documents at the earliest.\\n\\n"
        f"Regards,\\n"
        f"{firm_name}"
        + (f"\\nContact: {firm_mobile}" if firm_mobile else "")
    )


def build_whatsapp_queue():
    summary = get_reminder_summary()
    queue = []

    def add_task(task, reminder_label, priority):
        client = task.client
        queue.append({
            "task_id": task.id,
            "client_id": client.id,
            "client_name": client.client_name,
            "business_name": client.business_name,
            "mobile": client.mobile or "",
            "compliance_type": task.compliance_type,
            "form_name": task.form_name,
            "period": f"{task.period_month or ''} {task.period_year or ''}".strip(),
            "due_date": task.due_date.strftime("%d-%m-%Y") if task.due_date else "-",
            "status": task.status,
            "whatsapp_sent": task.whatsapp_sent,
            "whatsapp_sent_at": task.whatsapp_sent_at,
            "whatsapp_sent_by": task.whatsapp_sent_by,
            "reminder_label": reminder_label,
            "priority": priority,
            "message": build_whatsapp_message(task, reminder_label)
        })

    for task in summary["overdue"]:
        add_task(task, "overdue", "danger")

    for task in summary["due_today"]:
        add_task(task, "due today", "warning")

    for group in summary["upcoming_groups"]:
        for task in group["tasks"]:
            add_task(task, f"due in {group['days']} day{'s' if group['days'] != 1 else ''}", "info")

    return queue
