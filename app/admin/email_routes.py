from flask import render_template, request
from app.admin import admin_bp
from app.services.email_service import build_email_queue
from app.utils.route_guards import require_compliance_management


@admin_bp.route("/email-queue")
@require_compliance_management
def email_queue():
    queue = build_email_queue()

    search = request.args.get("search", "").strip().lower()
    reminder_type = request.args.get("reminder_type", "").strip()

    if search:
        queue = [
            item for item in queue
            if search in item["business_name"].lower()
            or search in item["client_name"].lower()
            or search in item["email"].lower()
            or search in item["form_name"].lower()
        ]

    if reminder_type:
        queue = [item for item in queue if item["priority"] == reminder_type]

    return render_template(
        "admin/email_queue.html",
        queue=queue,
        search=search,
        selected_reminder_type=reminder_type
    )
