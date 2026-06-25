from flask import render_template, redirect, url_for, session, request, flash
from app.admin import admin_bp
from app.database.db import db
from app.database.models import FirmSettings
from app.utils.route_guards import require_admin_area
from app.services.audit_service import log_action


@admin_bp.route("/settings", methods=["GET", "POST"])
@require_admin_area
def firm_settings():
    settings = FirmSettings.query.first()

    if not settings:
        settings = FirmSettings()
        db.session.add(settings)
        db.session.commit()

    if request.method == "POST":
        settings.firm_name = request.form.get("firm_name", "").strip()
        settings.tagline = request.form.get("tagline", "").strip()
        settings.proprietor_name = request.form.get("proprietor_name", "").strip()
        settings.mobile = request.form.get("mobile", "").strip()
        settings.email = request.form.get("email", "").strip()
        settings.website = request.form.get("website", "").strip()
        settings.address = request.form.get("address", "").strip()
        settings.city = request.form.get("city", "").strip()
        settings.state = request.form.get("state", "").strip()
        settings.pincode = request.form.get("pincode", "").strip()
        settings.gstin = request.form.get("gstin", "").strip().upper()
        settings.pan = request.form.get("pan", "").strip().upper()
        settings.financial_year = request.form.get("financial_year", "").strip()
        settings.reminder_days = request.form.get("reminder_days", "").strip()
        settings.primary_color = request.form.get("primary_color", "").strip()
        settings.accent_color = request.form.get("accent_color", "").strip()

        log_action(
            action="Updated",
            module="Firm Settings",
            record_type="FirmSettings",
            record_id=settings.id,
            description=f"Updated firm settings for {settings.firm_name}"
        )

        db.session.commit()
        flash("Firm settings updated successfully.", "success")
        return redirect(url_for("admin.firm_settings"))

    return render_template("admin/settings.html", settings=settings)
