from functools import wraps
from flask import session, redirect, url_for, flash
from app.utils.permissions import (
    is_admin_user,
    can_manage_clients,
    can_manage_staff,
    can_view_activity_log,
    can_manage_compliance
)


def require_admin_area(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_admin_user(session):
            flash("Access denied.", "error")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapper


def require_client_management(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not can_manage_clients(session):
            flash("You do not have permission to access Client Master.", "error")
            return redirect(url_for("admin.dashboard"))
        return view_func(*args, **kwargs)
    return wrapper


def require_staff_management(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not can_manage_staff(session):
            flash("You do not have permission to access Staff Master.", "error")
            return redirect(url_for("admin.dashboard"))
        return view_func(*args, **kwargs)
    return wrapper


def require_activity_log(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not can_view_activity_log(session):
            flash("You do not have permission to access Activity Log.", "error")
            return redirect(url_for("admin.dashboard"))
        return view_func(*args, **kwargs)
    return wrapper


def require_compliance_management(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not can_manage_compliance(session):
            flash("You do not have permission to access Compliance.", "error")
            return redirect(url_for("admin.dashboard"))
        return view_func(*args, **kwargs)
    return wrapper
