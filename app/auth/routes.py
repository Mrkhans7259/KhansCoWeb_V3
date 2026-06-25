from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.database.db import db
from app.database.models import User

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
            flash("Invalid email or password", "error")
            return redirect(url_for("auth.login"))

        if user.status != "active":
            flash("Your account is pending approval. Please contact Khans & Co.", "error")
            return redirect(url_for("auth.login"))

        session["user_id"] = user.id
        session["user_role"] = user.role
        session["user_name"] = user.name

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
    session.clear()
    return redirect(url_for("auth.login"))
