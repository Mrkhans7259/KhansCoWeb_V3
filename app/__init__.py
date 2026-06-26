from flask import Flask
from flask_migrate import Migrate
from config import Config
from app.database.db import db
from app.database.models import Notification
from app.utils.validation_hooks import init_validation_hooks

migrate = Migrate()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    init_validation_hooks(app)

    @app.context_processor
    def inject_notification_count():
        try:
            unread_notifications_count = Notification.query.filter_by(is_read=False).count()
        except Exception:
            unread_notifications_count = 0
        return dict(unread_notifications_count=unread_notifications_count)

    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.client.routes import client_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(client_bp)

    return app
