from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.database.db import db
from app.database.models import User
from app.services.audit_service import log_action

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            log_action(
                action="Failed Login",
                module="Authentication",
                description=f"Failed login attempt for email: {email}"
            )
            db.session.commit()
            flash("Invalid email or password", "error")
            return redirect(url_for("auth.login"))

        if user.status != "active":
            log_action(
                action="Blocked Login",
                module="Authentication",
                record_type="User",
                record_id=user.id,
                description=f"Blocked login for {user.email} with status {user.status}"
            )
            db.session.commit()
            flash("Your account is pending approval. Please contact Khans & Co.", "error")
            return redirect(url_for("auth.login"))

        session["user_id"] = user.id
        session["user_role"] = user.role
        session["user_name"] = user.name

        log_action(
            action="Login",
            module="Authentication",
            record_type="User",
            record_id=user.id,
            description=f"{user.role.title()} logged in: {user.email}"
        )
        db.session.commit()

        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("client.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/client/signup", methods=["GET", "POST"])
def client_signup():
    if request.method == "POST":
        user = User(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip().lower(),
            mobile=request.form.get("mobile", "").strip(),
            role="client",
            status="pending",
            business_name=request.form.get("business_name", "").strip(),
            gstin=request.form.get("gstin", "").strip().upper(),
            pan=request.form.get("pan", "").strip().upper()
        )

        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.client_signup"))

        if User.query.filter_by(email=user.email).first():
            flash("Email already registered", "error")
            return redirect(url_for("auth.client_signup"))

        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Client account created. Please wait for admin approval.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/client_signup.html")


@auth_bp.route("/forgot-password")
def forgot_password():
    return render_template("auth/forgot_password.html")


@auth_bp.route("/logout")
def logout():
    log_action(
        action="Logout",
        module="Authentication",
        description=f"{session.get('user_name')} logged out"
    )
    db.session.commit()
    session.clear()
    return redirect(url_for("auth.login"))
