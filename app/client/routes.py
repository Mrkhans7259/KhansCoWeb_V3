from flask import Blueprint, render_template, redirect, url_for, session

client_bp = Blueprint("client", __name__, url_prefix="/client")


@client_bp.route("/dashboard")
def dashboard():
    if session.get("user_role") != "client":
        return redirect(url_for("auth.login"))

    return render_template("client/dashboard.html")
