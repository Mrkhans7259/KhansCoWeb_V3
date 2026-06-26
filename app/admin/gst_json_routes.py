import os
import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename
from app.admin import admin_bp
from app.database.db import db
from app.database.models import Client, ClientDocument
from app.utils.route_guards import require_compliance_management
from app.services.gst_json_parser import parse_gst_json
from app.services.audit_service import log_action
from app.services.notification_service import create_notification


def gst_json_upload_root():
    root = os.path.join(current_app.root_path, "..", "uploads", "client_documents")
    os.makedirs(root, exist_ok=True)
    return root


def get_document_category(return_type):
    if return_type == "GSTR-1":
        return "GSTR-1"
    if return_type == "GSTR-3B":
        return "GSTR-3B"
    if return_type == "GSTR-2B":
        return "GSTR-2B"
    return "GST"


@admin_bp.route("/gst-json-import", methods=["GET", "POST"])
@require_compliance_management
def gst_json_import():
    parsed_data = None
    raw_preview = None
    matched_client = None
    document = None

    if request.method == "POST":
        file = request.files.get("gst_json")

        if not file or file.filename == "":
            flash("Please select a GST JSON file.", "error")
            return redirect(url_for("admin.gst_json_import"))

        if not file.filename.lower().endswith(".json"):
            flash("Only JSON files are allowed.", "error")
            return redirect(url_for("admin.gst_json_import"))

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        stored_filename = f"gstjson_{timestamp}_{filename}"
        save_path = os.path.join(gst_json_upload_root(), stored_filename)

        file.save(save_path)

        try:
            parsed_data = parse_gst_json(save_path)

            with open(save_path, "r", encoding="utf-8") as f:
                raw_preview = json.dumps(json.load(f), indent=2)[:3000]

        except Exception as error:
            flash(f"Invalid or unsupported GST JSON: {error}", "error")
            return redirect(url_for("admin.gst_json_import"))

        gstin = parsed_data.get("gstin")
        matched_client = Client.query.filter_by(gstin=gstin).first() if gstin and gstin != "-" else None

        if matched_client:
            category = get_document_category(parsed_data.get("return_type"))

            document = ClientDocument(
                client_id=matched_client.id,
                category=category,
                title=f"{parsed_data.get('return_type')} JSON - {parsed_data.get('period')} {parsed_data.get('financial_year')}",
                original_filename=filename,
                stored_filename=stored_filename,
                file_size=os.path.getsize(save_path),
                mime_type="application/json",
                notes=f"Imported GST JSON. GSTIN: {gstin}",
                uploaded_by=session.get("user_name")
            )

            db.session.add(document)
            db.session.flush()

            log_action(
                action="GST JSON Imported",
                module="GST JSON Import",
                record_type="ClientDocument",
                record_id=document.id,
                description=f"Imported {parsed_data.get('return_type')} JSON for {matched_client.business_name}"
            )

            create_notification(
                title="GST JSON Imported",
                message=f"{parsed_data.get('return_type')} JSON linked to {matched_client.business_name}.",
                notification_type="success",
                module="GST JSON Import",
                record_type="ClientDocument",
                record_id=document.id
            )

            db.session.commit()
            flash("GST JSON uploaded, parsed, and linked to client documents.", "success")

        else:
            log_action(
                action="GST JSON Uploaded Unmatched",
                module="GST JSON Import",
                description=f"GST JSON uploaded but no client matched GSTIN: {gstin}"
            )
            db.session.commit()
            flash("GST JSON parsed, but no matching client found for this GSTIN.", "error")

    return render_template(
        "admin/gst_json_import.html",
        parsed_data=parsed_data,
        raw_preview=raw_preview,
        matched_client=matched_client,
        document=document
    )
