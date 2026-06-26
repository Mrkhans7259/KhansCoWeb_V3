import os
from datetime import datetime
from flask import render_template, redirect, url_for, session, request, flash, send_from_directory, current_app
from werkzeug.utils import secure_filename
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Client, ClientDocument
from app.utils.route_guards import require_client_management
from app.services.audit_service import log_action
from app.services.notification_service import create_notification


ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "xlsx", "xls", "docx", "doc", "zip", "csv", "json"}
DOCUMENT_CATEGORIES = [
    "GST",
    "GSTR-1",
    "GSTR-3B",
    "GSTR-2B",
    "Income Tax",
    "TDS",
    "ROC",
    "PAN",
    "Aadhaar",
    "Bank Statements",
    "Invoices",
    "Agreements",
    "Financial Statements",
    "Other"
]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_root():
    root = os.path.join(current_app.root_path, "..", "uploads", "client_documents")
    os.makedirs(root, exist_ok=True)
    return root


@admin_bp.route("/documents")
@require_client_management
def all_documents():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = ClientDocument.query.join(Client)

    if search:
        query = query.filter(
            (Client.business_name.ilike(f"%{search}%")) |
            (Client.client_name.ilike(f"%{search}%")) |
            (Client.gstin.ilike(f"%{search}%")) |
            (ClientDocument.title.ilike(f"%{search}%")) |
            (ClientDocument.original_filename.ilike(f"%{search}%"))
        )

    if category:
        query = query.filter(ClientDocument.category == category)

    documents = query.order_by(ClientDocument.id.desc()).all()

    return render_template(
        "admin/documents.html",
        documents=documents,
        categories=DOCUMENT_CATEGORIES,
        search=search,
        selected_category=category
    )


@admin_bp.route("/clients/<int:client_id>/documents", methods=["GET", "POST"])
@require_client_management
def client_documents(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == "POST":
        file = request.files.get("document")
        category = request.form.get("category", "Other")
        title = request.form.get("title", "").strip()
        notes = request.form.get("notes", "").strip()

        if not file or file.filename == "":
            flash("Please select a document to upload.", "error")
            return redirect(url_for("admin.client_documents", client_id=client.id))

        if not allowed_file(file.filename):
            flash("File type not allowed.", "error")
            return redirect(url_for("admin.client_documents", client_id=client.id))

        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        stored_filename = f"client_{client.id}_{timestamp}_{original_filename}"

        save_path = os.path.join(upload_root(), stored_filename)
        file.save(save_path)

        document = ClientDocument(
            client_id=client.id,
            category=category,
            title=title or original_filename,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_size=os.path.getsize(save_path),
            mime_type=file.mimetype,
            notes=notes,
            uploaded_by=session.get("user_name")
        )

        db.session.add(document)
        db.session.flush()

        log_action(
            action="Uploaded",
            module="Documents",
            record_type="ClientDocument",
            record_id=document.id,
            description=f"Uploaded {document.original_filename} for {client.business_name}"
        )

        create_notification(
            title="Document Uploaded",
            message=f"{document.original_filename} uploaded for {client.business_name}.",
            notification_type="success",
            module="Documents",
            record_type="ClientDocument",
            record_id=document.id
        )

        db.session.commit()

        flash("Document uploaded successfully.", "success")
        return redirect(url_for("admin.client_documents", client_id=client.id))

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = ClientDocument.query.filter_by(client_id=client.id)

    if search:
        query = query.filter(
            (ClientDocument.title.ilike(f"%{search}%")) |
            (ClientDocument.original_filename.ilike(f"%{search}%")) |
            (ClientDocument.notes.ilike(f"%{search}%"))
        )

    if category:
        query = query.filter(ClientDocument.category == category)

    documents = query.order_by(ClientDocument.id.desc()).all()

    return render_template(
        "admin/client_documents.html",
        client=client,
        documents=documents,
        categories=DOCUMENT_CATEGORIES,
        search=search,
        selected_category=category
    )


@admin_bp.route("/documents/<int:document_id>/download")
@require_client_management
def download_document(document_id):
    document = ClientDocument.query.get_or_404(document_id)

    log_action(
        action="Downloaded",
        module="Documents",
        record_type="ClientDocument",
        record_id=document.id,
        description=f"Downloaded {document.original_filename} for {document.client.business_name}"
    )

    db.session.commit()

    return send_from_directory(
        upload_root(),
        document.stored_filename,
        as_attachment=True,
        download_name=document.original_filename
    )


@admin_bp.route("/documents/<int:document_id>/delete", methods=["POST"])
@require_client_management
def delete_document(document_id):
    document = ClientDocument.query.get_or_404(document_id)
    client_id = document.client_id
    client_name = document.client.business_name
    file_name = document.original_filename

    file_path = os.path.join(upload_root(), document.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    log_action(
        action="Deleted",
        module="Documents",
        record_type="ClientDocument",
        record_id=document.id,
        description=f"Deleted {file_name} for {client_name}"
    )

    create_notification(
        title="Document Deleted",
        message=f"{file_name} deleted for {client_name}.",
        notification_type="warning",
        module="Documents",
        record_type="ClientDocument",
        record_id=document.id
    )

    db.session.delete(document)
    db.session.commit()

    flash("Document deleted successfully.", "success")
    return redirect(url_for("admin.client_documents", client_id=client_id))
