from app import create_app
from app.database.db import db
from app.database.models import User

app = create_app()


def seed_database():
    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(email="admin@khansco.com").first()

        if not admin:
            admin = User(
                name="Khans & Co Admin",
                email="admin@khansco.com",
                mobile="9999999999",
                role="admin",
                status="active"
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created")
        else:
            print("✅ Admin user already exists")

        print("✅ Database ready")


if __name__ == "__main__":
    seed_database()
