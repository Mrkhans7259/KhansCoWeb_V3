from datetime import date
from flask import render_template, request, redirect, url_for, session, flash
from app.admin import admin_bp
from app.services.whatsapp_service import build_whatsapp_queue
from app.utils.route_guards import require_compliance_management
from app.database.db import db
from app.database.models import ComplianceTask
from app.services.audit_service import log_action
from app.services.notification_service import create_notification


@admin_bp.route("/whatsapp-queue")
@require_compliance_management
def whatsapp_queue():
    queue = build_whatsapp_queue()

    search = request.args.get("search", "").strip().lower()
    reminder_type = request.args.get("reminder_type", "").strip()
    send_status = request.args.get("send_status", "").strip()

    if search:
        queue = [
            item for item in queue
            if search in item["business_name"].lower()
            or search in item["client_name"].lower()
            or search in item["mobile"].lower()
            or search in item["form_name"].lower()
        ]

    if reminder_type:
        queue = [item for item in queue if item["priority"] == reminder_type]

    if send_status == "sent":
        queue = [item for item in queue if item["whatsapp_sent"]]

    if send_status == "pending":
        queue = [item for item in queue if not item["whatsapp_sent"]]

    if send_status == "sent_today":
        today = date.today()
        queue = [
            item for item in queue
            if item["whatsapp_sent"]
            and item["whatsapp_sent_at"]
            and item["whatsapp_sent_at"].date() == today
        ]

    return render_template(
        "admin/whatsapp_queue.html",
        queue=queue,
        search=search,
        selected_reminder_type=reminder_type,
        selected_send_status=send_status
    )


@admin_bp.route("/whatsapp-queue/<int:task_id>/mark-sent", methods=["POST"])
@require_compliance_management
def mark_whatsapp_sent(task_id):
    task = ComplianceTask.query.get_or_404(task_id)

    task.whatsapp_sent = True
    from datetime import datetime
    task.whatsapp_sent_at = datetime.now()
    task.whatsapp_sent_by = session.get("user_name")

    log_action(
        action="WhatsApp Sent",
        module="WhatsApp",
        record_type="ComplianceTask",
        record_id=task.id,
        description=f"Marked WhatsApp reminder as sent for {task.client.business_name} - {task.form_name}"
    )

    create_notification(
        title="WhatsApp Reminder Marked Sent",
        message=f"{task.form_name} reminder marked as sent for {task.client.business_name}.",
        notification_type="success",
        module="WhatsApp",
        record_type="ComplianceTask",
        record_id=task.id
    )

    db.session.commit()

    flash("WhatsApp reminder marked as sent.", "success")
    return redirect(url_for("admin.whatsapp_queue"))
