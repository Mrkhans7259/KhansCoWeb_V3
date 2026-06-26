from flask import render_template, redirect, url_for, session, request, flash
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Client, ClientDocument, ComplianceTask
from app.services.audit_service import log_action
from app.utils.duplicate_checks import check_client_duplicates
from app.utils.validators import clean, upper, validate_mobile, validate_email, validate_gstin, validate_pan, validate_pincode, collect_errors
from app.utils.route_guards import require_client_management


def admin_required():
    return session.get("user_role") == "admin"


def get_next_client_code():
    last_client = Client.query.order_by(Client.id.desc()).first()
    if not last_client:
        return "C001"
    return f"C{last_client.id + 1:03d}"


@admin_bp.route("/clients")
@require_client_management
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
@require_client_management
def add_client():
    if not admin_required():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        client = Client(client_code=get_next_client_code())
        try:
            save_client_from_form(client)
            duplicate_errors = check_client_duplicates(
                email=client.email,
                mobile=client.mobile,
                pan=client.pan,
                gstin=client.gstin
            )
            if duplicate_errors:
                raise ValueError("\n".join(duplicate_errors))
        except ValueError as error:
            for msg in str(error).split("\n"):
                flash(msg, "error")
            return render_template("admin/client_form.html", client=None)

        db.session.add(client)
        db.session.flush()

        log_action(
            action="Created",
            module="Client Management",
            record_type="Client",
            record_id=client.id,
            description=f"Created client: {client.business_name}"
        )

        db.session.commit()
        flash("Client added successfully", "success")
        return redirect(url_for("admin.clients"))

    return render_template("admin/client_form.html", client=None)


@admin_bp.route("/clients/<int:client_id>")
@require_client_management
def view_client(client_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    client = Client.query.get_or_404(client_id)

    documents_count = ClientDocument.query.filter_by(client_id=client.id).count()

    recent_documents = (
        ClientDocument.query
        .filter_by(client_id=client.id)
        .order_by(ClientDocument.id.desc())
        .limit(5)
        .all()
    )

    compliance_tasks = (
        ComplianceTask.query
        .filter_by(client_id=client.id)
        .order_by(ComplianceTask.id.desc())
        .all()
    )

    pending_tasks = [task for task in compliance_tasks if task.status == "pending"]
    filed_tasks = [task for task in compliance_tasks if task.status == "filed"]
    overdue_tasks = [task for task in compliance_tasks if task.status == "overdue"]

    dated_pending = [task for task in compliance_tasks if task.due_date and task.status != "filed"]
    next_due_task = sorted(dated_pending, key=lambda task: task.due_date)[0] if dated_pending else None

    recent_compliance_tasks = compliance_tasks[:5]

    return render_template(
        "admin/client_workspace.html",
        client=client,
        documents_count=documents_count,
        recent_documents=recent_documents,
        compliance_tasks=compliance_tasks,
        pending_tasks=pending_tasks,
        filed_tasks=filed_tasks,
        overdue_tasks=overdue_tasks,
        next_due_task=next_due_task,
        recent_compliance_tasks=recent_compliance_tasks
    )


@admin_bp.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
@require_client_management
def edit_client(client_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    client = Client.query.get_or_404(client_id)

    if request.method == "POST":
        try:
            save_client_from_form(client)
            duplicate_errors = check_client_duplicates(
                email=client.email,
                mobile=client.mobile,
                pan=client.pan,
                gstin=client.gstin
            )
            if duplicate_errors:
                raise ValueError("\n".join(duplicate_errors))
        except ValueError as error:
            for msg in str(error).split("\n"):
                flash(msg, "error")
            return render_template("admin/client_form.html", client=client)

        log_action(
            action="Updated",
            module="Client Management",
            record_type="Client",
            record_id=client.id,
            description=f"Updated client: {client.business_name}"
        )

        db.session.commit()
        flash("Client updated successfully", "success")
        return redirect(url_for("admin.view_client", client_id=client.id))

    return render_template("admin/client_form.html", client=client)


@admin_bp.route("/clients/<int:client_id>/delete", methods=["POST"])
@require_client_management
def delete_client(client_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("Client deleted successfully", "success")
    return redirect(url_for("admin.clients"))


def save_client_from_form(client):
    business_name = clean(request.form.get("business_name"))
    client_name = clean(request.form.get("client_name"))
    mobile = clean(request.form.get("mobile"))
    email = clean(request.form.get("email")).lower()
    gstin = upper(request.form.get("gstin"))
    pan = upper(request.form.get("pan"))
    pincode = clean(request.form.get("pincode"))

    errors = collect_errors(
        validate_mobile(mobile),
        validate_email(email),
        validate_gstin(gstin),
        validate_pan(pan),
        validate_pincode(pincode)
    )

    if errors:
        raise ValueError("\n".join(errors))

    client.business_name = business_name
    client.client_name = client_name
    client.mobile = mobile
    client.email = email
    client.gstin = gstin
    client.pan = pan
    client.constitution = clean(request.form.get("constitution"))
    client.registration_type = clean(request.form.get("registration_type"))
    client.return_frequency = clean(request.form.get("return_frequency"))
    client.address = clean(request.form.get("address"))
    client.city = clean(request.form.get("city"))
    client.state = clean(request.form.get("state"))
    client.pincode = pincode
    client.status = request.form.get("status", "active")
    client.assigned_staff = clean(request.form.get("assigned_staff"))
