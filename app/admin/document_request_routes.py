from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Client, DocumentRequest
from app.utils.route_guards import require_client_management
from app.services.notification_service import create_notification
from app.services.audit_service import log_action


DOCUMENT_TYPES = [
    "Bank Statement",
    "Purchase Register",
    "Sales Register",
    "GSTR-2B",
    "GSTR-1 Data",
    "GSTR-3B Data",
    "TDS Details",
    "Investment Proofs",
    "Salary Details",
    "Audit Documents",
    "Other"
]


@admin_bp.route("/clients/<int:client_id>/request-document", methods=["GET", "POST"])
@require_client_management
def request_document(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == "POST":
        document_name = request.form.get("document_name", "").strip()
        description = request.form.get("description", "").strip()
        due_date_text = request.form.get("due_date", "").strip()

        due_date = None
        if due_date_text:
            due_date = datetime.strptime(due_date_text, "%Y-%m-%d").date()

        if not document_name:
            flash("Please select document name.", "error")
            return redirect(url_for("admin.request_document", client_id=client.id))

        doc_req = DocumentRequest(
            client_id=client.id,
            document_name=document_name,
            description=description,
            due_date=due_date,
            status="Pending",
            requested_by=session.get("user_name")
        )

        db.session.add(doc_req)
        db.session.flush()

        create_notification(
            title="Document Requested",
            message=f"{document_name} requested from {client.business_name}.",
            notification_type="warning",
            module="Document Requests",
            record_type="DocumentRequest",
            record_id=doc_req.id
        )

        log_action(
            action="Requested",
            module="Document Requests",
            record_type="DocumentRequest",
            record_id=doc_req.id,
            description=f"Requested {document_name} from {client.business_name}"
        )

        db.session.commit()

        flash("Document request sent successfully.", "success")
        return redirect(url_for("admin.client_documents", client_id=client.id))

    return render_template(
        "admin/request_document.html",
        client=client,
        document_types=DOCUMENT_TYPES
    )


@admin_bp.route("/document-requests")
@require_client_management
def all_document_requests():
    status = request.args.get("status", "").strip()

    query = DocumentRequest.query

    if status:
        query = query.filter_by(status=status)

    requests = query.order_by(DocumentRequest.id.desc()).all()

    return render_template(
        "admin/document_requests.html",
        requests=requests,
        selected_status=status
    )


@admin_bp.route("/document-requests/<int:request_id>/status", methods=["POST"])
@require_client_management
def update_document_request_status(request_id):
    doc_req = DocumentRequest.query.get_or_404(request_id)
    status = request.form.get("status", "Pending")

    doc_req.status = status
    db.session.commit()

    flash("Document request status updated.", "success")
    return redirect(url_for("admin.all_document_requests"))
