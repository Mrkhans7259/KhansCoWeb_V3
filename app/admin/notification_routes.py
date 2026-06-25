from flask import render_template, redirect, url_for, session
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Notification


def admin_required():
    return session.get("user_role") == "admin"


@admin_bp.route("/notifications")
def notifications():
    if not admin_required():
        return redirect(url_for("auth.login"))

    notifications = Notification.query.order_by(Notification.id.desc()).limit(200).all()
    unread_count = Notification.query.filter_by(is_read=False).count()

    return render_template(
        "admin/notifications.html",
        notifications=notifications,
        unread_count=unread_count
    )


@admin_bp.route("/notifications/mark-all-read", methods=["POST"])
def mark_all_notifications_read():
    if not admin_required():
        return redirect(url_for("auth.login"))

    Notification.query.filter_by(is_read=False).update({"is_read": True})
    db.session.commit()

    return redirect(url_for("admin.notifications"))
