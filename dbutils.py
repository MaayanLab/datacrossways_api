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

def list_roles():
    db_roles = Role.query.all()
    print(db_roles)
    roles = []
    for role in db_roles:
        roles.append({"id": role.id, "name": role.name})
    return roles

# ===== files ========

def create_file(db, file_name, user_id):
    user = db.session.query(User).filter(User.id == user_id).first()
    file = File(name=file_name, user=user)
    db.session.add_all([file])
    db.session.commit()
    return {"id": file.id, "name": file.name, "display_name": file.name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner": file.owner_id}

def get_file(file_id):
    return File.query.filter_by(id=file_id).first()

def delete_file(file_id):
    File.query.filter_by(id=file_id).delete()

def list_all_files():
    #db_files = File.query.order_by(File.id).all()
    db_files = db.session.query(File, User.name).filter(File.owner_id == User.id).all()
    files = []
    for file in db_files:
        files.append({"id": file[0].id, "name": file[0].name, "display_name": file[0].display_name, "uuid": file[0].uuid, "status": file[0].status, "date": file[0].creation_date, "owner": file[0].owner_id, "owner_name": file[1], "visibility": file[0].visibility, "accessibility": file[0].accessibility})
    return files

def list_user_files(user_id):
    db_files = File.query.filter_by(owner_id=user_id).order_by(File.id).all()
    files = []
    for file in db_files:
        files.append({"id": file.id, "name": file.name, "display_name": file.display_name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner": file.owner_id, "visibility": file.visibility, "accessibility": file.accessibility})
    return files

def list_users():
    db_users = User.query.order_by(User.id).all()
    users = []
    for user in db_users:
        roles = get_user_roles(user.id)
        files = list_user_files(user.id)
        users.append({"id": user.id, "name": user.name, "uuid": user.uuid, "first_name": user.first_name, "last_name": user.last_name, "affiliation": user.affiliation,  "date": user.creation_date, "roles": roles, "files": files, "email": user.email})
    return users

def list_collections():
    db_collections = Collection.query.order_by(Collection.id).all()
    collections = []
    for collection in db_collections:
        collections.append({"id": collection.id, "name": collection.name, "uuid": collection.uuid, "parent_collection_id": collection.parent_collection_id, "date": collection.creation_date, "owner_id": collection.owner_id})
    return collections

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

def update_user(db, user, updater_id):
    print(user["id"])
    db_user = db.session.query(User).filter(User.id == user["id"]).first()
    db_user.firstname = user["first_name"]
    db_user.lastname = user["last_name"]
    db_user.email = user["email"]
    db_user.affiliation = user["affiliation"]

    newroles = []
    for r in user["roles"]:
        if user["roles"][r]:
            newroles.append(r)

    for role in db_user.roles:
        if role.name not in newroles:
            db_user.roles.remove(role)
    
    for role_name in newroles:
        role = Role.query.filter(Role.name==role_name).first()
        if role not in db_user.roles:
            db_user.roles.append(role)

    db.session.commit()

def update_file(db, file, updater_id):
    db_file = db.session.query(File).filter(File.id == file["id"]).first()
    db_file.display_name = file["display_name"]
    db_file.owner_id = file["owner"]
    #db_file.collection = file["collection"]
    db_file.visibility = file["visibility"]
    db_file.accessibility = file["accessibility"]
    db.session.commit()