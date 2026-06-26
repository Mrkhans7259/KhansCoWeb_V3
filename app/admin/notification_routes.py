from flask import render_template, redirect, url_for, session, request
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Notification


def admin_required():
    return session.get("user_role") in ["super_admin", "admin", "partner", "manager", "staff"]


@admin_bp.route("/notifications")
def notifications():
    if not admin_required():
        return redirect(url_for("auth.login"))

    status = request.args.get("status", "").strip()

    query = Notification.query

    if status == "unread":
        query = query.filter_by(is_read=False)

    if status == "read":
        query = query.filter_by(is_read=True)

    notifications = query.order_by(Notification.id.desc()).limit(300).all()
    unread_count = Notification.query.filter_by(is_read=False).count()

    return render_template(
        "admin/notifications.html",
        notifications=notifications,
        unread_count=unread_count,
        selected_status=status
    )


@admin_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    notification = Notification.query.get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()

    return redirect(url_for("admin.notifications"))


@admin_bp.route("/notifications/mark-all-read", methods=["POST"])
def mark_all_notifications_read():
    if not admin_required():
        return redirect(url_for("auth.login"))

    Notification.query.filter_by(is_read=False).update({"is_read": True})
    db.session.commit()

    return redirect(url_for("admin.notifications"))
