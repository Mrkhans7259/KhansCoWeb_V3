from flask import render_template, redirect, url_for, session, flash
from app.admin import admin_bp
from app.database.db import db
from app.database.models import User
from app.utils.route_guards import require_client_management


def get_next_client_code():
    last_client = Client.query.order_by(Client.id.desc()).first()
    if not last_client:
        return "C001"
    return f"C{last_client.id + 1:03d}"


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

    existing_client = None

    if user.gstin:
        existing_client = Client.query.filter_by(gstin=user.gstin).first()

    if not existing_client and user.email:
        existing_client = Client.query.filter_by(email=user.email).first()

    if not existing_client:
        new_client = Client(
            client_code=get_next_client_code(),
            business_name=user.business_name or user.name,
            client_name=user.name,
            mobile=user.mobile,
            email=user.email,
            gstin=user.gstin,
            pan=user.pan,
            status="active"
        )
        db.session.add(new_client)

    db.session.commit()

    flash("Client account approved and linked with Client Master successfully.", "success")
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
