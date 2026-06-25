from flask import render_template, redirect, url_for, session, request, flash
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Staff


def admin_required():
    return session.get("user_role") == "admin"


def get_next_staff_code():
    last_staff = Staff.query.order_by(Staff.id.desc()).first()
    if not last_staff:
        return "S001"
    return f"S{last_staff.id + 1:03d}"


@admin_bp.route("/staff")
def staff():
    if not admin_required():
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "").strip()
    query = Staff.query

    if search:
        query = query.filter(
            (Staff.name.ilike(f"%{search}%")) |
            (Staff.email.ilike(f"%{search}%")) |
            (Staff.mobile.ilike(f"%{search}%")) |
            (Staff.role.ilike(f"%{search}%")) |
            (Staff.designation.ilike(f"%{search}%"))
        )

    staff_members = query.order_by(Staff.id.desc()).all()
    return render_template("admin/staff.html", staff_members=staff_members, search=search)


@admin_bp.route("/staff/add", methods=["GET", "POST"])
def add_staff():
    if not admin_required():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        staff_member = Staff(staff_code=get_next_staff_code())
        save_staff_from_form(staff_member)

        db.session.add(staff_member)
        db.session.commit()

        flash("Staff added successfully", "success")
        return redirect(url_for("admin.staff"))

    return render_template("admin/staff_form.html", staff_member=None)


@admin_bp.route("/staff/<int:staff_id>/edit", methods=["GET", "POST"])
def edit_staff(staff_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    staff_member = Staff.query.get_or_404(staff_id)

    if request.method == "POST":
        save_staff_from_form(staff_member)
        db.session.commit()

        flash("Staff updated successfully", "success")
        return redirect(url_for("admin.staff"))

    return render_template("admin/staff_form.html", staff_member=staff_member)


@admin_bp.route("/staff/<int:staff_id>/delete", methods=["POST"])
def delete_staff(staff_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    staff_member = Staff.query.get_or_404(staff_id)
    db.session.delete(staff_member)
    db.session.commit()

    flash("Staff deleted successfully", "success")
    return redirect(url_for("admin.staff"))


def save_staff_from_form(staff_member):
    staff_member.name = request.form.get("name", "").strip()
    staff_member.email = request.form.get("email", "").strip().lower()
    staff_member.mobile = request.form.get("mobile", "").strip()
    staff_member.role = request.form.get("role", "staff").strip()
    staff_member.designation = request.form.get("designation", "").strip()
    staff_member.department = request.form.get("department", "").strip()
    staff_member.status = request.form.get("status", "active").strip()
    staff_member.address = request.form.get("address", "").strip()
