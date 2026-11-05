import os

from app import app, db
from models import Collection, Role, User


with app.app_context():
    db.create_all()

    # The root collection is the temporary destination for new uploads. Keep it
    # private even for databases created by versions where the default was open.
    root = Collection.query.filter_by(id=1).first()
    if root and root.accessibility != "locked":
        root.accessibility = "locked"
        db.session.commit()

    email = os.environ.get("ADMIN_EMAIL", "").strip()
    if email and User.query.filter_by(email=email).first() is None:
        user = User(
            name=f"{os.environ.get('ADMIN_FIRST_NAME', 'Admin')} {os.environ.get('ADMIN_LAST_NAME', 'User')}",
            first_name=os.environ.get("ADMIN_FIRST_NAME", "Admin"),
            last_name=os.environ.get("ADMIN_LAST_NAME", "User"),
            email=email,
        )
        user.roles.extend([Role(name="admin"), Role(name="uploader")])
        Collection(name="root", user=user, accessibility="locked")
        db.session.add(user)
        db.session.commit()
        print(f"Created initial administrator {email}")
