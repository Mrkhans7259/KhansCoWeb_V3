from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(30), nullable=False, default="client")
    status = db.Column(db.String(30), nullable=False, default="pending")

    business_name = db.Column(db.String(150), nullable=True)
    gstin = db.Column(db.String(20), nullable=True)
    pan = db.Column(db.String(20), nullable=True)

    reset_token = db.Column(db.String(120), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    client_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    business_name = db.Column(db.String(150), nullable=False)
    client_name = db.Column(db.String(120), nullable=False)

    mobile = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), nullable=True)

    gstin = db.Column(db.String(20), nullable=True, index=True)
    pan = db.Column(db.String(20), nullable=True, index=True)

    constitution = db.Column(db.String(80), nullable=True)
    registration_type = db.Column(db.String(80), nullable=True)
    return_frequency = db.Column(db.String(40), nullable=True)

    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(80), nullable=True)
    state = db.Column(db.String(80), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)

    status = db.Column(db.String(30), nullable=False, default="active")
    assigned_staff = db.Column(db.String(120), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship("ClientDocument", backref="client", cascade="all, delete-orphan")


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)

    staff_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(20), nullable=True)

    role = db.Column(db.String(50), nullable=False, default="staff")
    designation = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)

    status = db.Column(db.String(30), nullable=False, default="active")
    address = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClientDocument(db.Model):
    __tablename__ = "client_documents"

    id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)

    category = db.Column(db.String(80), nullable=False, default="Other")
    title = db.Column(db.String(180), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)

    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(120), nullable=True)

    notes = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.String(120), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ComplianceTask(db.Model):
    __tablename__ = "compliance_tasks"

    id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)

    compliance_type = db.Column(db.String(50), nullable=False, default="GST")
    form_name = db.Column(db.String(50), nullable=False)

    period_month = db.Column(db.String(20), nullable=True)
    period_year = db.Column(db.String(10), nullable=True)

    due_date = db.Column(db.Date, nullable=True)
    filing_date = db.Column(db.Date, nullable=True)

    status = db.Column(db.String(30), nullable=False, default="pending")

    arn = db.Column(db.String(100), nullable=True)
    assigned_staff = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    whatsapp_sent = db.Column(db.Boolean, default=False)
    whatsapp_sent_at = db.Column(db.DateTime, nullable=True)
    whatsapp_sent_by = db.Column(db.String(120), nullable=True)

    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    email_sent_by = db.Column(db.String(120), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship("Client", backref="compliance_tasks")



class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=True)
    user_name = db.Column(db.String(120), nullable=True)
    user_role = db.Column(db.String(50), nullable=True)

    action = db.Column(db.String(120), nullable=False)
    module = db.Column(db.String(80), nullable=False)

    record_type = db.Column(db.String(80), nullable=True)
    record_id = db.Column(db.Integer, nullable=True)

    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=True)

    notification_type = db.Column(db.String(50), nullable=False, default="info")
    module = db.Column(db.String(80), nullable=True)

    record_type = db.Column(db.String(80), nullable=True)
    record_id = db.Column(db.Integer, nullable=True)

    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class FirmSettings(db.Model):
    __tablename__ = "firm_settings"

    id = db.Column(db.Integer, primary_key=True)

    firm_name = db.Column(db.String(180), nullable=False, default="Khans & Co")
    tagline = db.Column(db.String(220), nullable=True, default="Compliance Manager Enterprise")

    proprietor_name = db.Column(db.String(150), nullable=True)
    mobile = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    website = db.Column(db.String(180), nullable=True)

    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(20), nullable=True)

    gstin = db.Column(db.String(30), nullable=True)
    pan = db.Column(db.String(30), nullable=True)

    financial_year = db.Column(db.String(20), nullable=True, default="2025-26")
    reminder_days = db.Column(db.String(100), nullable=True, default="15,7,3,1")

    primary_color = db.Column(db.String(20), nullable=True, default="#0f172a")
    accent_color = db.Column(db.String(20), nullable=True, default="#d4af37")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class ClientMessage(db.Model):
    __tablename__ = "client_messages"

    id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)

    subject = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False, default="General Query")
    priority = db.Column(db.String(30), nullable=False, default="Medium")

    message = db.Column(db.Text, nullable=False)

    attachment_filename = db.Column(db.String(255), nullable=True)
    attachment_stored_filename = db.Column(db.String(255), nullable=True)

    admin_reply = db.Column(db.Text, nullable=True)
    replied_by = db.Column(db.String(120), nullable=True)
    replied_at = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(30), nullable=False, default="Open")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship("Client", backref="messages")
