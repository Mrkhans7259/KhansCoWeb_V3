from flask import session
from app.database.db import db
from app.database.models import AuditLog


def log_action(action, module, record_type=None, record_id=None, description=None):
    log = AuditLog(
        user_id=session.get("user_id"),
        user_name=session.get("user_name"),
        user_role=session.get("user_role"),
        action=action,
        module=module,
        record_type=record_type,
        record_id=record_id,
        description=description
    )

    db.session.add(log)
