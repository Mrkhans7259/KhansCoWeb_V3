from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from app.database.db import db
from app.database.models import Client

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required():
    return session.get("user_role") == "admin"


def get_next_client_code():
    last_client = Client.query.order_by(Client.id.desc()).first()
    if not last_client:
        return "C001"

    next_id = last_client.id + 1
    return f"C{next_id:03d}"


@admin_bp.route("/dashboard")
def dashboard():
    if not admin_required():
        return redirect(url_for("auth.login"))

    total_clients = Client.query.count()
    active_clients = Client.query.filter_by(status="active").count()
    inactive_clients = Client.query.filter_by(status="inactive").count()

    return render_template(
        "admin/dashboard.html",
        total_clients=total_clients,
        active_clients=active_clients,
        inactive_clients=inactive_clients
    )


@admin_bp.route("/clients")
def clients():
    if not admin_required():
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "").strip()

    query = Client.query

    if search:
        query = query.filter(
            (Client.business_name.ilike(f"%{search}%")) |
            (Client.client_name.ilike(f"%{search}%")) |
            (Client.gstin.ilike(f"%{search}%")) |
            (Client.pan.ilike(f"%{search}%")) |
            (Client.mobile.ilike(f"%{search}%"))
        )

    clients = query.order_by(Client.id.desc()).all()

    return render_template("admin/clients.html", clients=clients, search=search)


@admin_bp.route("/clients/add", methods=["GET", "POST"])
def add_client():
    if not admin_required():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        client = Client(
            client_code=get_next_client_code(),
            business_name=request.form.get("business_name", "").strip(),
            client_name=request.form.get("client_name", "").strip(),
            mobile=request.form.get("mobile", "").strip(),
            email=request.form.get("email", "").strip(),
            gstin=request.form.get("gstin", "").strip().upper(),
            pan=request.form.get("pan", "").strip().upper(),
            constitution=request.form.get("constitution", "").strip(),
            registration_type=request.form.get("registration_type", "").strip(),
            return_frequency=request.form.get("return_frequency", "").strip(),
            address=request.form.get("address", "").strip(),
            city=request.form.get("city", "").strip(),
            state=request.form.get("state", "").strip(),
            pincode=request.form.get("pincode", "").strip(),
            status=request.form.get("status", "active"),
            assigned_staff=request.form.get("assigned_staff", "").strip()
        )

        db.session.add(client)
        db.session.commit()

        flash("Client added successfully", "success")
        return redirect(url_for("admin.clients"))

    return render_template("admin/client_form.html", client=None)
