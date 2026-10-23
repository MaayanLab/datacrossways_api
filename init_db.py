import os

from app import app, db
from models import Collection, Role, User


with app.app_context():
    db.create_all()

    email = os.environ.get("ADMIN_EMAIL", "").strip()
    if email and User.query.filter_by(email=email).first() is None:
        user = User(
            name=f"{os.environ.get('ADMIN_FIRST_NAME', 'Admin')} {os.environ.get('ADMIN_LAST_NAME', 'User')}",
            first_name=os.environ.get("ADMIN_FIRST_NAME", "Admin"),
            last_name=os.environ.get("ADMIN_LAST_NAME", "User"),
            email=email,
        )
        user.roles.extend([Role(name="admin"), Role(name="uploader")])
        Collection(name="root", user=user)
        db.session.add(user)
        db.session.commit()
        print(f"Created initial administrator {email}")
