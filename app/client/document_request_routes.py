import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename
from app.client.routes import client_bp, client_required, get_client_record
from app.database.db import db
from app.database.models import DocumentRequest, ClientDocument
from app.services.notification_service import create_notification
from app.services.audit_service import log_action


ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "xlsx", "xls", "docx", "doc", "csv", "json", "zip"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_root():
    root = os.path.join(current_app.root_path, "..", "uploads", "client_documents")
    os.makedirs(root, exist_ok=True)
    return root


@client_bp.route("/document-requests", methods=["GET"])
def document_requests():
    if not client_required():
        return redirect(url_for("auth.login"))

    user, client = get_client_record()

    if not client:
        flash("Your account is not linked with Client Master yet.", "error")
        return redirect(url_for("client.dashboard"))

    requests = DocumentRequest.query.filter_by(client_id=client.id).order_by(DocumentRequest.id.desc()).all()

    return render_template(
        "client/document_requests.html",
        user=user,
        client=client,
        requests=requests
    )


@client_bp.route("/document-requests/<int:request_id>/upload", methods=["POST"])
def upload_requested_document(request_id):
    if not client_required():
        return redirect(url_for("auth.login"))

    user, client = get_client_record()
    doc_req = DocumentRequest.query.get_or_404(request_id)

    if not client or doc_req.client_id != client.id:
        flash("Invalid document request.", "error")
        return redirect(url_for("client.dashboard"))

    file = request.files.get("document")

    if not file or file.filename == "":
        flash("Please select a document.", "error")
        return redirect(url_for("client.document_requests"))

    if not allowed_file(file.filename):
        flash("File type not allowed.", "error")
        return redirect(url_for("client.document_requests"))

    original_filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stored_filename = f"req_{doc_req.id}_client_{client.id}_{timestamp}_{original_filename}"

    save_path = os.path.join(upload_root(), stored_filename)
    file.save(save_path)

    client_doc = ClientDocument(
        client_id=client.id,
        category=doc_req.document_name,
        title=f"Requested: {doc_req.document_name}",
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size=os.path.getsize(save_path),
        mime_type=file.mimetype,
        notes=f"Uploaded against document request #{doc_req.id}",
        uploaded_by=user.name if user else "Client"
    )

    db.session.add(client_doc)

    doc_req.status = "Uploaded"
    doc_req.uploaded_filename = original_filename
    doc_req.uploaded_stored_filename = stored_filename
    doc_req.uploaded_at = datetime.now()

    db.session.flush()

    create_notification(
        title="Requested Document Uploaded",
        message=f"{client.business_name} uploaded {doc_req.document_name}.",
        notification_type="success",
        module="Document Requests",
        record_type="DocumentRequest",
        record_id=doc_req.id
    )

    log_action(
        action="Uploaded",
        module="Document Requests",
        record_type="DocumentRequest",
        record_id=doc_req.id,
        description=f"{client.business_name} uploaded requested document {doc_req.document_name}"
    )

    db.session.commit()

    flash("Requested document uploaded successfully.", "success")
    return redirect(url_for("client.document_requests"))
