import os
from datetime import datetime
from flask import render_template, redirect, url_for, session, request, flash, send_from_directory, current_app
from werkzeug.utils import secure_filename
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Client, ClientDocument


ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "xlsx", "xls", "docx", "doc", "zip", "csv"}
DOCUMENT_CATEGORIES = ["GST", "Income Tax", "TDS", "ROC", "PAN", "Aadhaar", "Bank", "Invoices", "Agreements", "Other"]


def admin_required():
    return session.get("user_role") == "admin"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_root():
    root = os.path.join(current_app.root_path, "..", "uploads", "client_documents")
    os.makedirs(root, exist_ok=True)
    return root


@admin_bp.route("/clients/<int:client_id>/documents", methods=["GET", "POST"])
def client_documents(client_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

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
        db.session.commit()

        flash("Document uploaded successfully.", "success")
        return redirect(url_for("admin.client_documents", client_id=client.id))

    documents = ClientDocument.query.filter_by(client_id=client.id).order_by(ClientDocument.id.desc()).all()

    return render_template(
        "admin/client_documents.html",
        client=client,
        documents=documents,
        categories=DOCUMENT_CATEGORIES
    )


@admin_bp.route("/documents/<int:document_id>/download")
def download_document(document_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    document = ClientDocument.query.get_or_404(document_id)
    return send_from_directory(
        upload_root(),
        document.stored_filename,
        as_attachment=True,
        download_name=document.original_filename
    )


@admin_bp.route("/documents/<int:document_id>/delete", methods=["POST"])
def delete_document(document_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    document = ClientDocument.query.get_or_404(document_id)
    client_id = document.client_id

    file_path = os.path.join(upload_root(), document.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(document)
    db.session.commit()

    flash("Document deleted successfully.", "success")
    return redirect(url_for("admin.client_documents", client_id=client_id))
