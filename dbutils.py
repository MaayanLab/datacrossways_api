from app import db, User, File, Collection, Role, UserRole
import json

def get_user(db, response):
    user_info = response.json()
    user = ""
    db_user = db.session.query(User).filter(User.email == user_info["email"]).first()
    if db_user:
        user = db_user
    else:
        db_user = User(user_info["name"], user_info["given_name"], user_info["family_name"], user_info["email"])
        db.session.add(db_user)
        db.session.commit()
        user = db.session.query(User).filter(User.email == user_info["email"]).first()
    return user

def create_user(user_info):
    user = User(name=user_info["name"], first_name=user_info["first_name"], last_name=user_info["last_name"], email=user_info["email"])
    db.session.add_all([user])
    db.session.commit()
    return {"id": user.id, "name": user.name, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "uuid": user.uuid, "date": user.creation_date}

def create_file(db, file_name, user_id):
    user = db.session.query(User).filter(User.id == user_id).first()
    file = File(name=file_name, user=user)
    db.session.add_all([file])
    db.session.commit()
    return {"id": file.id, "name": file.name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner": file.owner_id}

def list_user_files(user_id):
    db_files = File.query.filter_by(owner_id=user_id).all()
    files = []
    for file in db_files:
        files.append({"id": file.id, "name": file.name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner": file.owner_id})
    return files

def list_users():
    db_users = User.query.all()
    users = []
    for user in db_users:
        roles = get_user_roles(user.id)
        files = list_user_files(user.id)
        users.append({"id": user.id, "name": user.name, "uuid": user.uuid, "first_name": user.first_name, "last_name": user.last_name, "date": user.creation_date, "roles": roles, "files": files})
    return users

def get_file(file_id):
    return File.query.filter_by(id=file_id).first()

def delete_file(file_id):
    File.query.filter_by(id=file_id).delete()

def get_user_roles(userid):
    roles = []
    print("user_id: "+str(userid))
    for u, ur, r in db.session.query(User, UserRole, Role).filter(User.id == UserRole.user_id).filter(Role.id == UserRole.role_id).filter(User.id == userid).all():
        roles.append(r.name)
    roles = list(set(roles))
    return roles

def append_role(user_id, role_name):
    user = db.session.query(User).filter(User.id == user_id).first()
    role = Role.query.filter(Role.name==role_name).first()
    user.roles.append(role)
    db.session.commit()
