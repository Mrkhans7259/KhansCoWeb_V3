from datetime import datetime
from flask import render_template, redirect, url_for, session, request, flash
from app.admin import admin_bp
from app.database.db import db
from app.database.models import ClientMessage
from app.utils.route_guards import require_admin_area
from app.services.audit_service import log_action
from app.services.notification_service import create_notification


@admin_bp.route("/client-messages")
@require_admin_area
def client_messages():
    status = request.args.get("status", "").strip()
    search = request.args.get("search", "").strip()

    query = ClientMessage.query

    if status:
        query = query.filter(ClientMessage.status == status)

    if search:
        query = query.join(ClientMessage.client).filter(
            (ClientMessage.subject.ilike(f"%{search}%")) |
            (ClientMessage.message.ilike(f"%{search}%"))
        )

    messages = query.order_by(ClientMessage.id.desc()).all()

    return render_template(
        "admin/client_messages.html",
        messages=messages,
        selected_status=status,
        search=search
    )


@admin_bp.route("/client-messages/<int:message_id>", methods=["GET", "POST"])
@require_admin_area
def client_message_detail(message_id):
    msg = ClientMessage.query.get_or_404(message_id)

    if request.method == "POST":
        msg.admin_reply = request.form.get("admin_reply", "").strip()
        msg.status = request.form.get("status", "In Progress")
        msg.replied_by = session.get("user_name")
        msg.replied_at = datetime.now()
        msg.updated_at = datetime.now()

        log_action(
            action="Client Message Replied",
            module="Client Message Center",
            record_type="ClientMessage",
            record_id=msg.id,
            description=f"Replied to {msg.client.business_name}: {msg.subject}"
        )

        create_notification(
            title="Client Message Replied",
            message=f"Reply recorded for {msg.client.business_name}: {msg.subject}",
            notification_type="success",
            module="Client Message Center",
            record_type="ClientMessage",
            record_id=msg.id
        )

        db.session.commit()

        flash("Reply saved successfully.", "success")
        return redirect(url_for("admin.client_messages"))

    return render_template("admin/client_message_detail.html", msg=msg)
