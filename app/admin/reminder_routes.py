from flask import render_template
from app.admin import admin_bp
from app.services.reminder_service import get_reminder_summary
from app.utils.route_guards import require_compliance_management


@admin_bp.route("/reminders")
@require_compliance_management
def reminders():
    summary = get_reminder_summary()
    return render_template("admin/reminders.html", summary=summary)
