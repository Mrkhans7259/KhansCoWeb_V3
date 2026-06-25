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
