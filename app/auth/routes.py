from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.database.db import db
from app.database.models import User
from app.services.audit_service import log_action
from app.services.notification_service import create_notification
from app.utils.duplicate_checks import check_user_signup_duplicates
from app.utils.validators import validate_password

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
        name = request.form.get("name", "").strip()
        business_name = request.form.get("business_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        gstin = request.form.get("gstin", "").strip().upper()
        pan = request.form.get("pan", "").strip().upper()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        ok, password_error = validate_password(password)
        if not ok:
            flash(password_error, "error")
            return redirect(request.url)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(request.url)

        duplicate_errors = check_user_signup_duplicates(
            email=email,
            mobile=mobile,
            pan=pan,
            gstin=gstin
        )

        if duplicate_errors:
            for error in duplicate_errors:
                flash(error, "error")
            return redirect(request.url)

        user = User(
            name=name,
            business_name=business_name,
            email=email,
            mobile=mobile,
            gstin=gstin,
            pan=pan,
            role="client",
            status="pending"
        )
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        create_notification(
            title="New Client Signup",
            message=f"{business_name or name} has registered and is waiting for approval.",
            notification_type="warning",
            module="Client Signup",
            record_type="User",
            record_id=user.id
        )

        log_action(
            action="Client Signup",
            module="Authentication",
            record_type="User",
            record_id=user.id,
            description=f"New client signup pending approval: {business_name or name}"
        )

        db.session.commit()

        flash("Signup successful. Please wait for admin approval.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/client_signup.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    reset_link = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with this email.", "error")
            return redirect(url_for("auth.forgot_password"))

        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expiry = datetime.now() + timedelta(minutes=30)

        db.session.commit()

        reset_link = url_for("auth.reset_password", token=token, _external=True)
        flash("Password reset link generated. Use it within 30 minutes.", "success")

    return render_template("auth/forgot_password.html", reset_link=reset_link)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.now():
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        ok, password_error = validate_password(password)
        if not ok:
            flash(password_error, "error")
            return redirect(request.url)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(request.url)

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None

        db.session.commit()

        flash("Password reset successful. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html")

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


import secrets
from datetime import datetime, timedelta
