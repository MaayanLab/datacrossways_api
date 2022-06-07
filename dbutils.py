from app import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles, Accesskey
import json
import s3utils

def is_admin(user_id):
    user_roles = get_user_roles(user_id)
    if "admin" in set(user_roles):
        return True
    else:
        return False

def is_owner_file(user_id, file_id):
    file = get_file(file_id)
    if file.owner_id == user_id:
        return True
    else:
        return False

def is_owner_key(user_id, key_id):
    db_access_key = db.session.query(Accesskey).filter(Accesskey.id == key_id).first()
    if db_access_key.owner_id == user_id:
        return True
    else:
        return False

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

def create_file(db, file_name, file_size, user_id):
    user = db.session.query(User).filter(User.id == user_id).first()
    file = File(name=file_name, user=user, size=file_size)
    db.session.add_all([file])
    db.session.commit()
    return {"id": file.id, "name": file.name, "display_name": file.name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner_id": file.owner_id, "size": file.size}

def get_file(file_id):
    return File.query.filter_by(id=file_id).first()

def delete_file(file_id, user):
    if is_admin(user["id"]) or is_owner_file(user["id"], file_id):
        file = File.query.filter_by(id=file_id).first()
        s3utils.delete_file(file.uuid, file.name)
        db.session.delete(file)
        db.session.commit()
        return 1
    else:
        return 0

def list_all_files():
    #db_files = File.query.order_by(File.id).all()
    db_files = db.session.query(File, User.name).filter(File.owner_id == User.id).order_by(File.id).all()
    files = []
    for file in db_files:
        files.append({"id": file[0].id, "name": file[0].name, "display_name": file[0].display_name, "uuid": file[0].uuid, "status": file[0].status, "date": file[0].creation_date, "owner_id": file[0].owner_id, "owner_name": file[1], "visibility": file[0].visibility, "accessibility": file[0].accessibility, 'collection_id': file[0].collection_id, 'size': file[0].size})
    return files

def list_user_files(user_id):
    db_files = File.query.filter_by(owner_id=user_id).order_by(File.id).all()
    files = []
    for file in db_files:
        files.append({"id": file.id, "name": file.name, "display_name": file.display_name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner_id": file.owner_id, "visibility": file.visibility, "accessibility": file.accessibility, 'size': file.size})
    return files

def list_users():
    db_users = User.query.order_by(User.id).all()
    users = []
    for user in db_users:
        roles = get_user_roles(user.id)
        files = list_user_files(user.id)
        users.append({"id": user.id, "name": user.name, "uuid": user.uuid, "first_name": user.first_name, "last_name": user.last_name, "affiliation": user.affiliation,  "date": user.creation_date, "roles": roles, "files": files, "email": user.email})
    return users

def get_user_roles(userid):
    roles = []
    for u, ur, r in db.session.query(User, UserRole, Role).filter(User.id == UserRole.user_id).filter(Role.id == UserRole.role_id).filter(User.id == userid).all():
        roles.append({r.id, r.name})
    
    #for r in roles:
    #    db.session.query(Role, Policy).filter(Policy.id == ).all()
    return roles

#def get_user_scope(userid):


def append_role(user_id, role_name):
    user = db.session.query(User).filter(User.id == user_id).first()
    role = Role.query.filter(Role.name==role_name).first()
    user.roles.append(role)
    db.session.commit()

def update_user(db, user, updater_id):
    db_user = db.session.query(User).filter(User.id == user["id"]).first()
    db_user.firstname = user["first_name"]
    db_user.lastname = user["last_name"]
    db_user.email = user["email"]
    db_user.affiliation = user["affiliation"]
    
    db_user.roles = []
    for role in db.roles:
        role = Role.query.filter(Role.id==role.id).first()
        db_user.roles.append(role)

    db.session.commit()


def list_collections():
    db_collections = db.session.query(Collection, User.name).filter(Collection.owner_id == User.id).order_by(Collection.id).all()
    
    #db_collections = Collection.query.order_by(Collection.id).all()
    collections = []
    for collection in db_collections:
        collections.append({"id": collection[0].id, "name": collection[0].name, "uuid": collection[0].uuid, "parent_collection_id": collection[0].parent_collection_id, "date": collection[0].creation_date, "owner_id": collection[0].owner_id, "owner_name": collection[1]})
    return collections

def get_collection(collection_id, user_id):
    user_roles = get_user_roles(user_id)
    collection = Collection.query.filter(Collection.id==collection_id).first()
    sub_collections = Collection.query.filter(Collection.parent_collection_id==collection_id).order_by(Collection.id).all()
    collection_return = {"id": collection.id, "name": collection.name, "description": collection.description, "uuid": collection.uuid, "parent_collection_id": collection.parent_collection_id, "date": collection.creation_date, "owner_id": collection.owner_id, "child_collections": [], "child_files": []}
    
    sub_files = File.query.filter(File.collection_id==collection_id).order_by(File.id).all()
    
    for sc in sub_collections:
        num_collections = Collection.query.filter(Collection.parent_collection_id==sc.id).count()
        num_files = File.query.filter(File.collection_id==sc.id).count()
        temp_collection = {"id": sc.id, "name": sc.name, "uuid": sc.uuid, "parent_collection_id": sc.parent_collection_id, "date": sc.creation_date, "owner_id": sc.owner_id, "child_collections": num_collections, "child_files": num_files}
        collection_return["child_collections"].append(temp_collection)
    
    for file in sub_files:
        temp_file = {"id": file.id, "name": file.name, "display_name": file.display_name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner_id": file.owner_id, "visibility": file.visibility, "accessibility": file.accessibility, 'collection_id': file.collection_id, 'size': file.size}
        collection_return["child_files"].append(temp_file)
    
    return collection_return

def update_file(db, file, updater_id):
    db_file = db.session.query(File).filter(File.id == file["id"]).first()
    db_file.display_name = file["display_name"]
    db_file.owner_id = file["owner_id"]
    db_file.collection_id = file["collection_id"]
    db_file.visibility = file["visibility"]
    db_file.accessibility = file["accessibility"]
    db.session.commit()

def list_policies():
    db_policies = db.session.query(Policy).order_by(Policy.id).all()
    policies = []

    for policy in db_policies:
        
        file_res = db.session.query(File, PolicyFiles).filter(PolicyFiles.policy_id == policy.id).filter(File.id == PolicyFiles.file_id).all()
        files = []
        for file in file_res:
            print(file)
            files.append({"id": file[0].id, "name": file[0].name, "display_name": file[0].name, "uuid": file[0].uuid})
        
        collection_res = db.session.query(Collection, PolicyCollections).filter(PolicyCollections.policy_id == policy.id).filter(Collection.id == PolicyCollections.collection_id).all()
        collections = []
        for collection in collection_res:
            print("----")
            print(collection)
            print("----")
            collections.append({"id": collection[0].id, "name": collection[0].name, "uuid": collection[0].uuid})
        policies.append({"id": policy.id, "effect": policy.effect, "action": policy.action, "creation_date": policy.creation_date, "files": files, "collections": collections})
    
    return policies


def list_user_access_keys(user_id):
    db_access_keys = db.session.query(Accesskey).filter(Accesskey.owner_id == user_id).order_by(Accesskey.id).all()
    access_keys = []
    for key in db_access_keys:
        access_keys.append({"id": key.id, "expiration_time": key.expiration_time, "creation_date": key.creation_date, "uuid": key.uuid});

    return access_keys

def create_access_key(user_id, expiration_time):
    user = db.session.query(User).filter(User.id == user_id).first()
    akey = Accesskey(user=user, expiration_time=expiration_time)
    db.session.add(akey)
    db.session.commit()

def delete_access_key(user_id, key_id):
    if is_admin(user_id) or is_owner_key(user_id, key_id):
        db_access_key = db.session.query(Accesskey).filter(Accesskey.id == key_id).first()
        db.session.delete(db_access_key)
        db.session.commit()
        return 1
    else:
        return 0

def get_key_user(user_key):
    akey = db.session.query(Accesskey).filter(Accesskey.uuid == user_key).first()
    user = db.session.query(User).filter(User.id == akey.owner_id).first()
    return user
