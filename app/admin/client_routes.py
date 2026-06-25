from flask import render_template, redirect, url_for, session, request, flash
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Client


def admin_required():
    return session.get("user_role") == "admin"


def get_next_client_code():
    last_client = Client.query.order_by(Client.id.desc()).first()
    if not last_client:
        return "C001"
    return f"C{last_client.id + 1:03d}"


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
        client = Client(client_code=get_next_client_code())
        save_client_from_form(client)
        db.session.add(client)
        db.session.commit()
        flash("Client added successfully", "success")
        return redirect(url_for("admin.clients"))

    return render_template("admin/client_form.html", client=None)


@admin_bp.route("/clients/<int:client_id>")
def view_client(client_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    client = Client.query.get_or_404(client_id)
    return render_template("admin/client_profile.html", client=client)


@admin_bp.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
def edit_client(client_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    client = Client.query.get_or_404(client_id)

    if request.method == "POST":
        save_client_from_form(client)
        db.session.commit()
        flash("Client updated successfully", "success")
        return redirect(url_for("admin.view_client", client_id=client.id))

    return render_template("admin/client_form.html", client=client)


@admin_bp.route("/clients/<int:client_id>/delete", methods=["POST"])
def delete_client(client_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("Client deleted successfully", "success")
    return redirect(url_for("admin.clients"))


def save_client_from_form(client):
    client.business_name = request.form.get("business_name", "").strip()
    client.client_name = request.form.get("client_name", "").strip()
    client.mobile = request.form.get("mobile", "").strip()
    client.email = request.form.get("email", "").strip()
    client.gstin = request.form.get("gstin", "").strip().upper()
    client.pan = request.form.get("pan", "").strip().upper()
    client.constitution = request.form.get("constitution", "").strip()
    client.registration_type = request.form.get("registration_type", "").strip()
    client.return_frequency = request.form.get("return_frequency", "").strip()
    client.address = request.form.get("address", "").strip()
    client.city = request.form.get("city", "").strip()
    client.state = request.form.get("state", "").strip()
    client.pincode = request.form.get("pincode", "").strip()
    client.status = request.form.get("status", "active")
    client.assigned_staff = request.form.get("assigned_staff", "").strip()
