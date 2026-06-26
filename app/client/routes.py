import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from app.database.db import db
from app.database.models import User, Client, ComplianceTask, ClientDocument, Notification, FirmSettings, ClientMessage
from app.utils.validators import clean, upper, validate_mobile, validate_gstin, validate_pan, collect_errors
from app.utils.route_guards import require_admin_area
from app.services.audit_service import log_action
from app.services.notification_service import create_notification

client_bp = Blueprint("client", __name__, url_prefix="/client")


def client_required():
    return session.get("user_role") == "client"


def get_client_record():
    user = None

    user_id = session.get("user_id")
    user_email = session.get("user_email")

    if user_id:
        user = User.query.get(user_id)

    if not user and user_email:
        user = User.query.filter_by(email=user_email).first()

    if not user:
        return None, None

    client = None

    if user.gstin:
        client = Client.query.filter_by(gstin=user.gstin).first()

    if not client and user.email:
        client = Client.query.filter_by(email=user.email).first()

    return user, client


@client_bp.route("/dashboard")
def dashboard():
    if not client_required():
        return redirect(url_for("auth.login"))

    user, client = get_client_record()

    compliance_tasks = []
    documents = []

    if client:
        compliance_tasks = ComplianceTask.query.filter_by(client_id=client.id).order_by(ComplianceTask.id.desc()).limit(10).all()
        documents = ClientDocument.query.filter_by(client_id=client.id).order_by(ClientDocument.id.desc()).limit(10).all()

    firm_settings = FirmSettings.query.first()

    return render_template(
        "client/dashboard.html",
        user=user,
        client=client,
        compliance_tasks=compliance_tasks,
        documents=documents,
        firm_settings=firm_settings
    )


@client_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if not client_required():
        return redirect(url_for("auth.login"))

    user, client = get_client_record()

    if not user:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        name = clean(request.form.get("name"))
        mobile = clean(request.form.get("mobile"))
        business_name = clean(request.form.get("business_name"))
        gstin = upper(request.form.get("gstin"))
        pan = upper(request.form.get("pan"))

        errors = collect_errors(
            validate_mobile(mobile),
            validate_gstin(gstin),
            validate_pan(pan)
        )

        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("client.profile"))

        user.name = name
        user.mobile = mobile
        user.business_name = business_name
        user.gstin = gstin
        user.pan = pan

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("client.profile"))

    return render_template("client/profile.html", user=user, client=client)


ALLOWED_CLIENT_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "xlsx", "xls", "docx", "doc", "zip", "csv", "json"}

CLIENT_DOCUMENT_CATEGORIES = [
    "GST",
    "GSTR-1",
    "GSTR-3B",
    "GSTR-2B",
    "Income Tax",
    "TDS",
    "ROC",
    "Bank Statements",
    "Invoices",
    "Other"
]


def client_upload_root():
    root = os.path.join(current_app.root_path, "..", "uploads", "client_documents")
    os.makedirs(root, exist_ok=True)
    return root


def allowed_client_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_CLIENT_EXTENSIONS


@client_bp.route("/documents", methods=["GET", "POST"])
def documents():
    if not client_required():
        return redirect(url_for("auth.login"))

    user, client = get_client_record()

    if not client:
        flash("Your account is not linked with Client Master yet. Please contact Khans & Co.", "error")
        return redirect(url_for("client.dashboard"))

    if request.method == "POST":
        file = request.files.get("document")
        category = request.form.get("category", "Other")
        title = request.form.get("title", "").strip()
        notes = request.form.get("notes", "").strip()

        if not file or file.filename == "":
            flash("Please select a document.", "error")
            return redirect(url_for("client.documents"))

        if not allowed_client_file(file.filename):
            flash("File type not allowed.", "error")
            return redirect(url_for("client.documents"))

        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        stored_filename = f"client_{client.id}_{timestamp}_{original_filename}"

        save_path = os.path.join(client_upload_root(), stored_filename)
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
            uploaded_by=user.name
        )

        db.session.add(document)
        db.session.flush()

        log_action(
            action="Client Uploaded",
            module="Client Portal Documents",
            record_type="ClientDocument",
            record_id=document.id,
            description=f"Client uploaded {document.original_filename} for {client.business_name}"
        )

        create_notification(
            title="Client Document Uploaded",
            message=f"{client.business_name} uploaded {document.original_filename}.",
            notification_type="success",
            module="Client Portal",
            record_type="ClientDocument",
            record_id=document.id
        )

        db.session.commit()

        flash("Document uploaded successfully.", "success")
        return redirect(url_for("client.documents"))

    documents = ClientDocument.query.filter_by(client_id=client.id).order_by(ClientDocument.id.desc()).all()

    return render_template(
        "client/documents.html",
        user=user,
        client=client,
        documents=documents,
        categories=CLIENT_DOCUMENT_CATEGORIES
    )


CLIENT_MESSAGE_CATEGORIES = [
    "GST",
    "Income Tax",
    "TDS",
    "ROC",
    "Bank Statement",
    "Documents",
    "Fees",
    "General Query"
]


@client_bp.route("/messages", methods=["GET", "POST"])
def messages():
    if not client_required():
        return redirect(url_for("auth.login"))

    user, client = get_client_record()

    if not client:
        flash("Your account is not linked with Client Master yet. Please contact Khans & Co.", "error")
        return redirect(url_for("client.dashboard"))

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        category = request.form.get("category", "General Query").strip()
        priority = request.form.get("priority", "Medium").strip()
        message_text = request.form.get("message", "").strip()

        if not subject or not message_text:
            flash("Subject and message are required.", "error")
            return redirect(url_for("client.messages"))

        msg = ClientMessage(
            client_id=client.id,
            subject=subject,
            category=category,
            priority=priority,
            message=message_text,
            status="Open"
        )

        db.session.add(msg)
        db.session.flush()

        log_action(
            action="Client Message Sent",
            module="Client Message Center",
            record_type="ClientMessage",
            record_id=msg.id,
            description=f"{client.business_name} sent message: {subject}"
        )

        create_notification(
            title="New Client Message",
            message=f"{client.business_name}: {subject}",
            notification_type="warning",
            module="Client Message Center",
            record_type="ClientMessage",
            record_id=msg.id
        )

        db.session.commit()

        flash("Message sent successfully.", "success")
        return redirect(url_for("client.messages"))

    messages = ClientMessage.query.filter_by(client_id=client.id).order_by(ClientMessage.id.desc()).all()

    return render_template(
        "client/messages.html",
        user=user,
        client=client,
        messages=messages,
        categories=CLIENT_MESSAGE_CATEGORIES
    )
