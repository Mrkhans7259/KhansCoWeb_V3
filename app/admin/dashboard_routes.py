from flask import render_template, redirect, url_for, session
from app.admin import admin_bp
from app.database.models import Client
from app.utils.route_guards import require_admin_area


def admin_required():
    return session.get("user_role") == "admin"


@admin_bp.route("/dashboard")
@require_admin_area
def dashboard():
    if not admin_required():
        return redirect(url_for("auth.login"))

    return render_template(
        "admin/dashboard.html",
        total_clients=Client.query.count(),
        active_clients=Client.query.filter_by(status="active").count(),
        inactive_clients=Client.query.filter_by(status="inactive").count()
    )
