from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from app.admin import dashboard_routes
from app.admin import client_routes
from app.admin import staff_routes
from app.admin import approval_routes
from app.admin import document_routes
from app.admin import compliance_routes

from app.admin import activity_routes

from app.admin import notification_routes

from app.admin import settings_routes

from app.admin import reminder_routes

from app.admin import whatsapp_routes
