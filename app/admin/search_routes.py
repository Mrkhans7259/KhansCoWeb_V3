from flask import render_template, request
from app.admin import admin_bp
from app.database.models import Client, Staff, ComplianceTask, Notification
from app.utils.route_guards import require_admin_area


@admin_bp.route("/global-search")
@require_admin_area
def global_search():
    q = request.args.get("q", "").strip()

    clients = []
    staff = []
    tasks = []
    notifications = []

    if q:
        clients = Client.query.filter(
            (Client.business_name.ilike(f"%{q}%")) |
            (Client.client_name.ilike(f"%{q}%")) |
            (Client.gstin.ilike(f"%{q}%")) |
            (Client.pan.ilike(f"%{q}%")) |
            (Client.mobile.ilike(f"%{q}%"))
        ).limit(10).all()

        staff = Staff.query.filter(
            (Staff.name.ilike(f"%{q}%")) |
            (Staff.email.ilike(f"%{q}%")) |
            (Staff.mobile.ilike(f"%{q}%")) |
            (Staff.role.ilike(f"%{q}%"))
        ).limit(10).all()

        tasks = ComplianceTask.query.join(Client).filter(
            (Client.business_name.ilike(f"%{q}%")) |
            (Client.gstin.ilike(f"%{q}%")) |
            (ComplianceTask.form_name.ilike(f"%{q}%")) |
            (ComplianceTask.compliance_type.ilike(f"%{q}%")) |
            (ComplianceTask.period_month.ilike(f"%{q}%")) |
            (ComplianceTask.period_year.ilike(f"%{q}%"))
        ).limit(10).all()

        notifications = Notification.query.filter(
            (Notification.title.ilike(f"%{q}%")) |
            (Notification.message.ilike(f"%{q}%")) |
            (Notification.module.ilike(f"%{q}%"))
        ).limit(10).all()

    return render_template(
        "admin/global_search.html",
        q=q,
        clients=clients,
        staff=staff,
        tasks=tasks,
        notifications=notifications
    )
