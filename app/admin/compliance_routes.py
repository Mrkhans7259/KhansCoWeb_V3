from datetime import datetime
from flask import render_template, redirect, url_for, session, request, flash
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Client, ComplianceTask


def admin_required():
    return session.get("user_role") == "admin"


@admin_bp.route("/compliance")
def compliance_dashboard():
    if not admin_required():
        return redirect(url_for("auth.login"))

    tasks = ComplianceTask.query.order_by(ComplianceTask.id.desc()).all()

    return render_template(
        "admin/compliance.html",
        tasks=tasks
    )


@admin_bp.route("/clients/<int:client_id>/compliance/add", methods=["GET", "POST"])
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
        db.session.commit()

        flash("Compliance task added successfully.", "success")
        return redirect(url_for("admin.compliance_dashboard"))

    return render_template("admin/compliance_form.html", client=client, task=None)


@admin_bp.route("/compliance/<int:task_id>/edit", methods=["GET", "POST"])
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

        db.session.commit()

        flash("Compliance task updated successfully.", "success")
        return redirect(url_for("admin.compliance_dashboard"))

    return render_template("admin/compliance_form.html", client=task.client, task=task)


@admin_bp.route("/compliance/<int:task_id>/delete", methods=["POST"])
def delete_compliance_task(task_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    task = ComplianceTask.query.get_or_404(task_id)

    db.session.delete(task)
    db.session.commit()

    flash("Compliance task deleted successfully.", "success")
    return redirect(url_for("admin.compliance_dashboard"))
