from datetime import datetime
from flask import render_template, redirect, url_for, session, request, flash
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Client, ComplianceTask
from app.services.audit_service import log_action
from app.services.notification_service import create_notification
from app.utils.route_guards import require_compliance_management


def admin_required():
    return session.get("user_role") == "admin"


@admin_bp.route("/compliance")
@require_compliance_management
def compliance_dashboard():
    if not admin_required():
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "").strip()
    compliance_type = request.args.get("compliance_type", "").strip()
    status = request.args.get("status", "").strip()
    period_month = request.args.get("period_month", "").strip()
    period_year = request.args.get("period_year", "").strip()

    query = ComplianceTask.query.join(Client)

    if search:
        query = query.filter(
            (Client.business_name.ilike(f"%{search}%")) |
            (Client.client_name.ilike(f"%{search}%")) |
            (Client.gstin.ilike(f"%{search}%")) |
            (Client.pan.ilike(f"%{search}%")) |
            (ComplianceTask.form_name.ilike(f"%{search}%"))
        )

    if compliance_type:
        query = query.filter(ComplianceTask.compliance_type == compliance_type)

    if status:
        query = query.filter(ComplianceTask.status == status)

    if period_month:
        query = query.filter(ComplianceTask.period_month == period_month)

    if period_year:
        query = query.filter(ComplianceTask.period_year == period_year)

    tasks = query.order_by(ComplianceTask.id.desc()).all()

    total_tasks = len(tasks)
    pending_tasks = len([task for task in tasks if task.status == "pending"])
    filed_tasks = len([task for task in tasks if task.status == "filed"])
    overdue_tasks = len([task for task in tasks if task.status == "overdue"])

    return render_template(
        "admin/compliance.html",
        tasks=tasks,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        filed_tasks=filed_tasks,
        overdue_tasks=overdue_tasks,
        search=search,
        selected_type=compliance_type,
        selected_status=status,
        selected_month=period_month,
        selected_year=period_year
    )


@admin_bp.route("/clients/<int:client_id>/compliance/add", methods=["GET", "POST"])
@require_compliance_management
def add_compliance_task(client_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    client = Client.query.get_or_404(client_id)

    if request.method == "POST":
        task = ComplianceTask(
            client_id=client.id,
            compliance_type=request.form.get("compliance_type", "GST"),
            form_name=request.form.get("form_name", "").strip(),
            period_month=request.form.get("period_month", "").strip(),
            period_year=request.form.get("period_year", "").strip(),
            status=request.form.get("status", "pending"),
            arn=request.form.get("arn", "").strip(),
            assigned_staff=request.form.get("assigned_staff", "").strip(),
            notes=request.form.get("notes", "").strip()
        )

        due_date = request.form.get("due_date", "").strip()
        filing_date = request.form.get("filing_date", "").strip()

        if due_date:
            task.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()

        if filing_date:
            task.filing_date = datetime.strptime(filing_date, "%Y-%m-%d").date()

        db.session.add(task)
        db.session.flush()

        log_action(
            action="Created",
            module="Compliance",
            record_type="ComplianceTask",
            record_id=task.id,
            description=f"Created {task.form_name} for {client.business_name} ({task.period_month} {task.period_year})"
        )

        create_notification(
            title="Compliance Task Created",
            message=f"{task.form_name} created for {client.business_name} ({task.period_month} {task.period_year})",
            notification_type="success",
            module="Compliance",
            record_type="ComplianceTask",
            record_id=task.id
        )

        db.session.commit()

        flash("Compliance task added successfully.", "success")
        return redirect(url_for("admin.view_client", client_id=client.id))

    return render_template("admin/compliance_form.html", client=client, task=None)


@admin_bp.route("/compliance/<int:task_id>/edit", methods=["GET", "POST"])
@require_compliance_management
def edit_compliance_task(task_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    task = ComplianceTask.query.get_or_404(task_id)

    if request.method == "POST":
        task.compliance_type = request.form.get("compliance_type", "GST")
        task.form_name = request.form.get("form_name", "").strip()
        task.period_month = request.form.get("period_month", "").strip()
        task.period_year = request.form.get("period_year", "").strip()
        task.status = request.form.get("status", "pending")
        task.arn = request.form.get("arn", "").strip()
        task.assigned_staff = request.form.get("assigned_staff", "").strip()
        task.notes = request.form.get("notes", "").strip()

        due_date = request.form.get("due_date", "").strip()
        filing_date = request.form.get("filing_date", "").strip()

        task.due_date = datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else None
        task.filing_date = datetime.strptime(filing_date, "%Y-%m-%d").date() if filing_date else None

        log_action(
            action="Updated",
            module="Compliance",
            record_type="ComplianceTask",
            record_id=task.id,
            description=f"Updated {task.form_name} for {task.client.business_name} ({task.period_month} {task.period_year})"
        )

        create_notification(
            title="Compliance Task Updated",
            message=f"{task.form_name} updated for {task.client.business_name} ({task.period_month} {task.period_year})",
            notification_type="info",
            module="Compliance",
            record_type="ComplianceTask",
            record_id=task.id
        )

        db.session.commit()

        flash("Compliance task updated successfully.", "success")
        return redirect(url_for("admin.compliance_dashboard"))

    return render_template("admin/compliance_form.html", client=task.client, task=task)


@admin_bp.route("/compliance/<int:task_id>/delete", methods=["POST"])
@require_compliance_management
def delete_compliance_task(task_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    task = ComplianceTask.query.get_or_404(task_id)

    task_id_value = task.id
    task_description = f"{task.form_name} for {task.client.business_name} ({task.period_month} {task.period_year})"

    log_action(
        action="Deleted",
        module="Compliance",
        record_type="ComplianceTask",
        record_id=task_id_value,
        description=f"Deleted {task_description}"
    )

    create_notification(
        title="Compliance Task Deleted",
        message=f"Deleted {task_description}",
        notification_type="danger",
        module="Compliance",
        record_type="ComplianceTask",
        record_id=task_id_value
    )

    db.session.delete(task)
    db.session.commit()

    flash("Compliance task deleted successfully.", "success")
    return redirect(url_for("admin.compliance_dashboard"))


@admin_bp.route("/compliance/generate-gst", methods=["GET", "POST"])
@require_compliance_management
def generate_gst_tasks():
    if not admin_required():
        return redirect(url_for("auth.login"))

    clients = Client.query.filter_by(status="active").order_by(Client.business_name.asc()).all()

    if request.method == "POST":
        client_ids = request.form.getlist("client_ids")
        period_month = request.form.get("period_month", "").strip()
        period_year = request.form.get("period_year", "").strip()
        due_date_text = request.form.get("due_date", "").strip()
        assigned_staff = request.form.get("assigned_staff", "").strip()
        forms = request.form.getlist("forms")

        if not client_ids:
            flash("Please select at least one client.", "error")
            return redirect(url_for("admin.generate_gst_tasks"))

        if not forms:
            flash("Please select at least one GST form.", "error")
            return redirect(url_for("admin.generate_gst_tasks"))

        due_date = datetime.strptime(due_date_text, "%Y-%m-%d").date() if due_date_text else None
        created_count = 0
        skipped_count = 0

        for client_id in client_ids:
            for form_name in forms:
                existing = ComplianceTask.query.filter_by(
                    client_id=client_id,
                    compliance_type="GST",
                    form_name=form_name,
                    period_month=period_month,
                    period_year=period_year
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                task = ComplianceTask(
                    client_id=client_id,
                    compliance_type="GST",
                    form_name=form_name,
                    period_month=period_month,
                    period_year=period_year,
                    due_date=due_date,
                    status="pending",
                    assigned_staff=assigned_staff,
                    notes="Auto generated GST task"
                )

                db.session.add(task)
                created_count += 1

        log_action(
            action="Bulk GST Generate",
            module="Compliance",
            record_type="ComplianceTask",
            description=f"Generated {created_count} GST tasks for {period_month} {period_year}. Skipped duplicates: {skipped_count}."
        )

        create_notification(
            title="Bulk GST Tasks Generated",
            message=f"Generated {created_count} GST tasks for {period_month} {period_year}. Skipped duplicates: {skipped_count}.",
            notification_type="success",
            module="Compliance",
            record_type="ComplianceTask"
        )

        db.session.commit()

        flash(f"GST tasks generated: {created_count}. Skipped duplicates: {skipped_count}.", "success")
        return redirect(url_for("admin.compliance_dashboard"))

    return render_template("admin/generate_gst.html", clients=clients)
