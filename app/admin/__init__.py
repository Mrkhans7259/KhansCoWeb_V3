from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from app.admin import dashboard_routes
from app.admin import client_routes
from app.admin import staff_routes
