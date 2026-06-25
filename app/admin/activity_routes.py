from flask import render_template, redirect, url_for, session
from app.admin import admin_bp
from app.database.models import AuditLog
from app.utils.route_guards import require_activity_log


def admin_required():
    return session.get("user_role") == "admin"


@admin_bp.route("/activity")
@require_activity_log
def activity_log():
    if not admin_required():
        return redirect(url_for("auth.login"))

    logs = AuditLog.query.order_by(AuditLog.id.desc()).limit(200).all()

    return render_template("admin/activity.html", logs=logs)
