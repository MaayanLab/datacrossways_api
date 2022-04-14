from app import db, User, File, Collection, Role, UserRole

File.query.filter_by(id=11).first().update(status="deleted")

File.query.filter_by(id=7).delete()
db.session.commit()

file_count = File.query.filter_by(owner_id=1).count()

File.query.filter_by(owner_id=2).all()

File.query.filter_by(id=11).first().update(status="deleted")
db.session.commit()

db.session.query(Role)

from app import db, User, File, Collection, Role, UserRole
UserRole.query.filter_by(user_id=1)

res = db.session.query(
    UserRole.role_id,
    Role.id
).join(
    UserRole,
    UserRole.id == Role.id
).first()

print(file_count)

Role.query.filter(Role.name=="Admin").first()

from app import db, User, File, Collection, Role, UserRole
for u, ur, r in db.session.query(User, UserRole, Role).filter(User.id == UserRole.user_id).filter(Role.id == UserRole.id).filter(User.id == 2).all():
    print(u.name+" - "+str(ur.id)+" - "+r.name)


from app import db, User, File, Collection, Role, UserRole
for u, ur, r in db.session.query(User, UserRole, Role).filter(User.id == UserRole.user_id).filter(Role.id == UserRole.role_id).filter(User.id == 3).all():
    print(u.name+" - "+str(ur.id)+" - "+r.name)


# attach an existing role to existing user
from app import db, User, File, Collection, Role, UserRole
user_id = 3
role_name = "Admin"
user = db.session.query(User).filter(User.id == user_id).first()
role = Role.query.filter(Role.name==role_name).first()
user.roles.append(role)
db.session.commit()


# list all users
from app import db, User, File, Collection, Role, UserRole
users = User.query.all()
for u in users:
    print(u)
