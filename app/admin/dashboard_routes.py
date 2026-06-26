from flask import render_template
from app.admin import admin_bp
from app.database.models import Client, Staff, ComplianceTask, Notification, AuditLog
from app.services.reminder_service import get_reminder_summary
from app.utils.route_guards import require_admin_area


@admin_bp.route("/dashboard")
@require_admin_area
def dashboard():
    reminder_summary = get_reminder_summary()

    total_clients = Client.query.count()
    active_clients = Client.query.filter_by(status="active").count()
    total_staff = Staff.query.count()

    total_tasks = ComplianceTask.query.count()
    pending_tasks = ComplianceTask.query.filter_by(status="pending").count()
    filed_tasks = ComplianceTask.query.filter_by(status="filed").count()
    overdue_tasks = len(reminder_summary["overdue"])

    unread_notifications = Notification.query.filter_by(is_read=False).count()

    recent_activity = AuditLog.query.order_by(AuditLog.id.desc()).limit(8).all()
    recent_notifications = Notification.query.order_by(Notification.id.desc()).limit(6).all()

    return render_template(
        "admin/dashboard.html",
        total_clients=total_clients,
        active_clients=active_clients,
        total_staff=total_staff,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        filed_tasks=filed_tasks,
        overdue_tasks=overdue_tasks,
        due_today_count=reminder_summary["due_today_count"],
        upcoming_count=reminder_summary["upcoming_count"],
        unread_notifications=unread_notifications,
        recent_activity=recent_activity,
        recent_notifications=recent_notifications,
    )
