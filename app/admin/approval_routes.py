from flask import render_template, redirect, url_for, session, flash
from app.admin import admin_bp
from app.database.db import db
from app.database.models import User
from app.utils.route_guards import require_client_management


def admin_required():
    return session.get("user_role") == "admin"


@admin_bp.route("/client-approvals")
@require_client_management
def client_approvals():
    if not admin_required():
        return redirect(url_for("auth.login"))

    pending_clients = User.query.filter_by(role="client", status="pending").order_by(User.id.desc()).all()
    approved_clients = User.query.filter_by(role="client", status="active").order_by(User.id.desc()).all()
    rejected_clients = User.query.filter_by(role="client", status="rejected").order_by(User.id.desc()).all()

    return render_template(
        "admin/client_approvals.html",
        pending_clients=pending_clients,
        approved_clients=approved_clients,
        rejected_clients=rejected_clients
    )


@admin_bp.route("/client-approvals/<int:user_id>/approve", methods=["POST"])
@require_client_management
def approve_client(user_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(user_id)

    if user.role != "client":
        flash("Only client accounts can be approved.", "error")
        return redirect(url_for("admin.client_approvals"))

    user.status = "active"
    db.session.commit()

    flash("Client account approved successfully.", "success")
    return redirect(url_for("admin.client_approvals"))


@admin_bp.route("/client-approvals/<int:user_id>/reject", methods=["POST"])
@require_client_management
def reject_client(user_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(user_id)

    if user.role != "client":
        flash("Only client accounts can be rejected.", "error")
        return redirect(url_for("admin.client_approvals"))

    user.status = "rejected"
    db.session.commit()

    flash("Client account rejected.", "success")
    return redirect(url_for("admin.client_approvals"))
