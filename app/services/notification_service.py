from app.database.db import db
from app.database.models import Notification


def create_notification(title, message=None, notification_type="info", module=None, record_type=None, record_id=None):
    notification = Notification(
        title=title,
        message=message,
        notification_type=notification_type,
        module=module,
        record_type=record_type,
        record_id=record_id
    )

    db.session.add(notification)
    return notification
