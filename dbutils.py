import traceback
from app import db, session, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles, Accesskey
import json
import jsonschema
from jsonschema import validate
import s3utils
from datetime import datetime
from sqlalchemy.types import Integer, Float
import time
from sqlalchemy import or_

def is_admin(user_id):
    user_roles = get_user_roles(user_id)
    for r in user_roles:
        if r["name"] == "admin":
            return True
    return False

def is_uploader(user_id):
    user_roles = get_user_roles(user_id)
    for r in user_roles:
        if r["name"] == "uploader":
            return True
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

def get_stats():
    file_count = db.session.query(File.id).count()
    collection_count = db.session.query(Collection.id).filter(Collection.visibility == "visible").count()
    file_sizes = db.session.query(File.size).all()
    file_size_sum = 0
    for file_size in file_sizes:
        file_size_sum = file_size_sum+file_size[0]
    return {"files": file_count, "datasets": collection_count, "size": file_size_sum}

def get_user_by_id_json(id):
    db_user = db.session.query(User).filter(User.id == id).first()
    user = ""
    if db_user:
        role_list = []
        for role in db_user.roles:
            role_list.append(role.name)   
        user = {"id": db_user.id, "name": db_user.name, "first_name": db_user.first_name, "last_name": db_user.last_name, "email": db_user.email, "affiliation": db_user.affiliation, "creation_date": db_user.creation_date, "uuid": db_user.uuid, "storage_quota": db_user.storage_quota, "roles": role_list}
    return user

def get_user_by_id(id):
    db_user = db.session.query(User).filter(User.id == id).first()
    user = ""
    if db_user:
        user = db_user
    return user

def get_user(db, user_info):
    user = ""
    if user_info.get("orcid_id") != None:
        db_user = db.session.query(User).filter(User.orcid_id == user_info["orcid_id"]).first()
        if db_user:
            user = db_user
        else:
            db_user = User(user_info["name"], user_info["first_name"], user_info["last_name"], user_info["email"], orcid_id=user_info["orcid_id"])
            db.session.add(db_user)
            db.session.commit()
            user = db.session.query(User).filter(User.orcid_id == user_info["orcid_id"]).first()
    else:
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
    if db.session.query(User).filter(User.email == user_info["email"]).first() is None:
        #collections = user_info.get("collections", None)
        #files = user_info.get("files", None)
        #roles = user_info.get("collections", None)
        #user_info.pop("collections", None)
        #user_info.pop("files", None)
        #user_info.pop("roles", None)
        user = User(**user_info)
        user.orcid_id = None
        #user.collections = db.session.query(Collection).filter(Collection.id.in_(collections)).all()
        #user.files  = db.session.query(File).filter(File.id.in_(files)).all()
        #user.roles = db.session.query(Role).filter(Role.id.in_(roles)).all()

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return(print_user(user))
    else:
        raise Exception("User already exists")

def delete_user(user_id):
    dbuser = db.session.query(User).filter(User.id == user_id).first()
    r = print_user(dbuser)
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return(r)

def list_user_quota(user_id):
    db_user = db.session.query(User).filter(User.id == user_id).first()
    db_files = db.session.query(File).filter(File.owner_id == user_id).all()
    quota_used = 0
    for file in db_files:
        quota_used = quota_used+file.size
    quota_used = quota_used/(1024*1024)
    return((int(quota_used), int(max(0, db_user.storage_quota - quota_used)), int(db_user.storage_quota)))

def update_user(user):
    dbuser = db.session.query(User).filter(User.id == user["id"]).first()
    user.pop("creation_date", None)
    user.pop("uuid", None)
    user.pop("id", None)

    #collections = user["collections"]
    #files = user["files"]
    #roles = user["roles"]
    #user.pop("collections", None)
    #user.pop("files", None)
    #user.pop("roles", None)

    #dbuser.collections = list(set(dbuser.collections + db.session.query(Collection).filter(Collection.id.in_(collections)).all()))
    #dbuser.files  = list(set(dbuser.files + db.session.query(File).filter(File.id.in_(files)).all()))
    #dbuser.roles = list(set(dbuser.roles + db.session.query(Role).filter(Role.id.in_(roles)).all()))

    if "name" in user:
        dbuser.name = user["name"]
    if "first_name" in user:
        dbuser.first_name = user["first_name"]
    if "last_name" in user:
        dbuser.last_name = user["last_name"]
    if "email" in user:
        dbuser.email = user["email"]
    if "affiliation" in user:
        dbuser.affiliation = user["affiliation"]

    db.session.commit()

    return(print_user(dbuser))

# ----------- roles ----------------

def delete_role(role_id):
    dbrole = db.session.query(Role).filter(Role.id == role_id).first()
    r = print_role(dbrole)
    Role.query.filter_by(id=role_id).delete()
    db.session.commit()
    return(r)

def update_role(data):
    overwrite = False
    role = data["role"]
    dbrole = db.session.query(Role).filter(Role.id == role["id"]).first()

    dbpolicies = db.session.query(Policy).all()
    dbp = []
    for p in dbpolicies:
        dbp.append(p.id)

    if "overwrite" in data.keys():
        overwrite = data["overwrite"]

    if "name" in data["role"].keys():
        dbrole.name = data["role"]["name"]

    if overwrite:
        dbrole.policies = []
        for p in role["policies"]:
            if p in dbp:
                pp = db.session.query(Policy).filter(Policy.id == p).first()
                dbrole.policies.append(pp)
    else:
        for p in role["policies"]:
            if p in dbp and p not in dbrole.policies:
                pp = db.session.query(Policy).filter(Policy.id == p).first()
                dbrole.policies.append(pp)
    db.session.commit()
    return(print_role(dbrole))

def create_role(role_name, policies=[]):
    if db.session.query(Role).filter(Role.name == role_name).first() is None:
        role = Role(name=role_name)
        for p in policies:
            policy = db.session.query(Policy).filter(Policy.id == p).first()
            role.policies.append(policy)
        db.session.add_all([role])
        db.session.commit()
        db.session.refresh(role)
        return(print_role(role))
    else:
        raise Exception("Role name already exists. Choose a different name")

def list_roles():
    db_roles = Role.query.all()
    roles = []
    for role in db_roles:
        r = print_role(role)
        roles.append(r)
    return roles

def print_role(role):
    policies = []
    if role.policies is not None:
        for policy in role.policies:
            pp = print_policy(policy)
            policies.append(pp)
    return({"id": role.id, "name": role.name, "policies": policies})

def print_policy(policy):
    pp = dict(policy.__dict__)
    pp.pop('_sa_instance_state', None)

    files = []
    collections = []
    for collection in policy.collections:
        c = dict(collection.__dict__)
        c.pop('_sa_instance_state', None)
        collections.append(c["id"])

    files = []
    for file in policy.files:
        f = dict(file.__dict__)
        f.pop('_sa_instance_state', None)
        files.append(f["id"])
    pp["collections"] = collections
    pp["files"] = files
    return(pp)

# ===== files ========

def create_file(db, file_name, file_size, user_id):
    user = db.session.query(User).filter(User.id == user_id).first()
    file = File(name=file_name, user=user, size=file_size, collection_id=1)
    db.session.add_all([file])
    db.session.commit()
    db.session.refresh(file)
    return {"id": file.id, "name": file.name, "display_name": file.name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner_id": file.owner_id, "owner_name": user.name, "size": file.size, "accessibility": file.accessibility, "visibility": file.visibility, "collection_id": file.collection_id}

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

def list_files(offset, limit):
    db_files = db.session.query(File, User.name).filter(File.owner_id == User.id).order_by(File.id).offset(offset).limit(limit).all()
    file_count = db.session.query(File.id).filter(File.owner_id == User.id).count()
    files = []
    for file in db_files:
        files.append({"id": file[0].id, "name": file[0].name, "display_name": file[0].display_name, "uuid": file[0].uuid, "status": file[0].status, "date": file[0].creation_date, "owner_id": file[0].owner_id, "owner_name": file[1], "visibility": file[0].visibility, "accessibility": file[0].accessibility, 'collection_id': file[0].collection_id, 'size': file[0].size})
    return files, file_count

def list_files_detail(offset, limit):
    db_files = db.session.query(File, User, Collection).filter(File.owner_id == User.id).filter(File.collection_id == Collection.id).order_by(File.id).offset(offset).limit(limit).all()
    file_count = db.session.query(File.id).filter(File.owner_id == User.id).count()
    files = []
    for file in db_files:
        owner = file[1]
        collection = file[2]
        owner_result = {"first_name": owner.first_name, "last_name": owner.last_name, "id": owner.id, "uuid": owner.uuid}
        collection_result = {"id": collection.id, "name": collection.name, "uuid": collection.uuid}
        file_result = {"id": file[0].id, "name": file[0].name, "display_name": file[0].display_name, "uuid": file[0].uuid, "status": file[0].status, "date": file[0].creation_date, "owner": owner_result, "visibility": file[0].visibility, "accessibility": file[0].accessibility, 'collection': collection_result, 'size': file[0].size}
        files.append(file_result)
    return files, file_count

def list_user_files(user_id, offset, limit):
    #file_count = File.query.filter_by(File.owner_id=user_id).order_by(File.id).count()
    file_count = db.session.query(File).filter(File.owner_id == user_id).count()
    #db_files = File.query.filter_by(owner_id=user_id).order_by(File.id).offset(offset).limit(limit).all()
    db_files = db.session.query(File, User, Collection).filter(File.owner_id == user_id).filter(File.owner_id == User.id).filter(File.collection_id == Collection.id).order_by(File.id).offset(offset).limit(limit).all()
    files = []
    for file in db_files:
        owner = file[1]
        collection = file[2]
        owner_result = {"first_name": owner.first_name, "last_name": owner.last_name, "id": owner.id, "uuid": owner.uuid}
        collection_result = {"id": collection.id, "name": collection.name, "uuid": collection.uuid}
        file_result = {"id": file[0].id, "name": file[0].name, "display_name": file[0].display_name, "uuid": file[0].uuid, "status": file[0].status, "date": file[0].creation_date, "owner": owner_result, "visibility": file[0].visibility, "accessibility": file[0].accessibility, 'collection': collection_result, 'size': file[0].size}
        files.append(file_result)
    return files, file_count

def list_user_collections(user_id, offset, limit):
    collection_count = db.session.query(Collection).filter(Collection.owner_id == user_id).count()
    db_collections = db.session.query(Collection).filter(Collection.owner_id == user_id).order_by(Collection.id).offset(offset).limit(limit).all()
    collections = []
    for collection in db_collections:
        collections.append(print_collection(collection))
    return collections, collection_count

def list_collection_files(user_id):
    return []

def search_files(data, user_id, collection_id, file_name, owner_id, offset=0, limit=20):
    tt = time.time()
    (list_creds, read_creds, write_creds) = get_scope(user_id)
    print(time.time()-tt)
    tt = time.time()

    files = db.session.query(File)
    if collection_id is not None:
        files = files.filter(File.collection_id == collection_id)
    else:
        #files = filterjson(db.session.query(File), File.meta, data).all()
        files = filterjson(db.session.query(File), File.meta, data)
    
    if file_name is not None:
        files = files.filter(or_(File.display_name.like("%{}%".format(file_name)), File.description.like("%{}%".format(file_name))))
    
    if owner_id is not None:
        files = files.filter(File.owner_id == owner_id)
    
    files = filterjson(files, File.meta, data)

    print(time.time()-tt)
    
    res_files = []
    tt = time.time()
    for file in files:
        if file.uuid in list_creds or file.visibility == "visible" or is_admin(user_id):
            permissions = ["list"]
            if file.uuid in read_creds:
                permissions.append("read")
            if file.uuid in write_creds:
                permissions.append("write")
            f = dict(file.__dict__)
            f.pop('_sa_instance_state', None)
            res_files.append(f)
    #print(len(res_files))
    print(time.time()-tt)
    res_files_page = res_files[offset:(offset+limit)]

    return add_file_detail(res_files_page), len(res_files)

def add_file_detail(files):
    for file in files:
        file_details = db.session.query(File, User, Collection).filter(File.id == file["id"]).filter(File.owner_id == User.id).filter(File.collection_id == Collection.id).all()[0]
        #print(file_details)
        owner = {"id": file_details[1].id, "first_name": file_details[1].first_name, "last_name": file_details[1].last_name}
        collection = {"id": file_details[2].id, "name": file_details[2].name}
        file["owner"] = owner
        file["collection"] = collection
    return files

def list_users():
    db_users = User.query.order_by(User.id).all()
    users = []
    for user in db_users:
        users.append(print_user(user))
    return users

def get_user_roles(userid):
    roles = []
    for u, ur, r in db.session.query(User, UserRole, Role).filter(User.id == UserRole.user_id).filter(Role.id == UserRole.role_id).filter(User.id == userid).all():
        roles.append({"id": r.id, "name": r.name})
    #print(roles)
    return roles

def print_user(user):
    roles = []
    for r in user.roles:
        roles.append(r.id)
    files = []
    for f in user.files:
        files.append(f.id)
    collections = []
    for c in user.collections:
        collections.append(c.id)
    user = dict(user.__dict__)
    user.pop('_sa_instance_state', None)
    user["files"] = files
    user["roles"] = roles
    user["collections"] = collections
    return(user)

def print_file():
    return({})

def print_collection(collection):
    collections = [c.id for c in collection.collections]
    files = [f.id for f in collection.files]
    collection = dict(collection.__dict__)
    collection.pop('_sa_instance_state', None)
    collection["collections"] = collections
    collection["files"] = files
    return(collection)

def get_scope(userid):
    read_cred = []
    write_cred = []
    list_cred = []
    return (set(list_cred), set(read_cred), set(write_cred))

def get_scope2(userid):
    read_cred = []
    write_cred = []
    list_cred = []
    roles = []
    for u, ur, r in db.session.query(User, UserRole, Role).filter(User.id == UserRole.user_id).filter(Role.id == UserRole.role_id).filter(User.id == userid).all():
        roles.append(r)
        for p in r.policies:
            if p.effect == "allow":
                for c in p.collections:
                    add_collection_scope(c, p.action, list_cred, read_cred, write_cred)
    return (set(list_cred), set(read_cred), set(write_cred))

def add_collection_scope(collection, action, list_cred, read_cred, write_cred):
    for f in collection.files:
        if action == "list":
            list_cred.append(f.uuid)
        elif action == "write":
            write_cred.append(f.uuid)
        elif action == "read":
            read_cred.append(f.uuid)
    for c in collection.collections:
        add_collection_scope(c, action, list_cred, read_cred, write_cred)
        if action == "list":
            list_cred.append(c.uuid)
        elif action == "write":
            write_cred.append(c.uuid)
        elif action == "read":
            read_cred.append(c.uuid)

def append_role(user_id, role_name):
    user = db.session.query(User).filter(User.id == user_id).first()
    role = Role.query.filter(Role.name==role_name).first()
    user.roles.append(role)
    db.session.commit()

def list_collections():
    db_collections = Collection.query.all()
    
    #db_collections = Collection.query.order_by(Collection.id).all()
    collections = []
    for collection in db_collections:
        collections.append(print_collection(collection))
    return collections

def create_collection(collection, user_id):
    collection.pop("collections", None)
    collection.pop("files", None)
    collection.pop("id", None)
    collection.pop("uuid", None)
    collection["owner_id"] = user_id
    if "parent_collection_id" in collection:
        if not db.session.query(Collection).filter(Collection.id == collection["parent_collection_id"]).first():
            raise Exception("Invalid parent, collection does not exist")
    else:
        collection["parent_collection_id"] = 1
    dbcollection = Collection(**collection)
    db.session.add_all([dbcollection])
    db.session.commit()
    db.session.refresh(dbcollection)
    return(print_collection(dbcollection))

def update_collection(collection):
    dbcollection = db.session.query(Collection).filter(Collection.id == collection["id"]).first()
    collection.pop("creation_date", None)
    collection.pop("uuid", None)
    collection.pop("id", None)
    collections = collection.pop("collections", [])
    parent_path = get_parent_collection_path(dbcollection.id)
    for cid in collections:
        if cid in [x.id for x in parent_path]:
            raise Exception("Invalid child, child collection is also parent (circular collection path).")
    files = collection.pop("files", [])
    overwrite = collection.pop("overwrite", False)
    print(files)
    if overwrite:
        for c in dbcollection.collections:
            if c.id not in collections:
                c.parent_collection_id = 1
        for f in dbcollection.files:
            if f.id not in files:
                f.collection_id = 1
        dbcollection.collections = db.session.query(Collection).filter(Collection.id.in_(collections)).all()
        dbcollection.files = db.session.query(File).filter(File.id.in_(files)).all()
    else:
        dbcollection.collections = list(set(dbcollection.collections + db.session.query(Collection).filter(Collection.id.in_(collections)).all()))
        dbcollection.files  = list(set(dbcollection.files + db.session.query(File).filter(File.id.in_(files)).all()))

    if "name" in collection:
        dbcollection.name = collection["name"]
    if "description" in collection:
        dbcollection.description = collection["description"]
    if "image_url" in collection:
        dbcollection.image_url = collection["image_url"]
    if "visibility" in collection:
        dbcollection.visibility = collection["visibility"]
    if "affiliation" in collection:
        dbcollection.affiliation = collection["affiliation"]
    if "owner_id" in collection:
        dbcollection.owner_id = collection["owner_id"]
    if "parent_collection_id" in collection:
        dbcollection.parent_collection_id = collection["parent_collection_id"]
    if "visibility" in collection:
        dbcollection.visibility = collection["visibility"]
    if "accessibility" in collection:
        dbcollection.accessibility = collection["accessibility"]
    
    db.session.commit()
    db.session.refresh(dbcollection)
    return(print_collection(dbcollection))

def delete_collection(collection_id):
    dbcollection = db.session.query(Collection).filter(Collection.id == collection_id).first()
    c = print_collection(dbcollection)
    Collection.query.filter(id == collection_id).delete()
    db.session.commit()
    return(c)

def get_collection(collection_id, user_id):
    (list_creds, read_creds, write_creds) = get_scope(user_id)
    #collection = Collection.query.filter(Collection.id==collection_id).first()
    query_result = db.session.query(Collection, User).filter(Collection.id==collection_id).filter(User.id == Collection.owner_id).first()
    collection = query_result[0]
    db_owner = query_result[1]
    owner = {"id": db_owner.id, "name": db_owner.name, "firstname": db_owner.first_name, "lastname": db_owner.last_name, "affiliation": db_owner.affiliation}
    sub_collections = Collection.query.filter(Collection.parent_collection_id==collection_id).order_by(Collection.id).all()
    sub_files = File.query.filter(File.collection_id==collection_id).order_by(File.id).all()
    collection_return = {"id": collection.id, "name": collection.name, "description": collection.description, "uuid": collection.uuid, "parent_collection_id": collection.parent_collection_id, "date": collection.creation_date, "owner_id": collection.owner_id, "owner": owner, "image_url": collection.image_url, "collections": len(sub_collections), "child_collections": [], "files": len(sub_files), "accessibility": collection.accessibility, "visibility": collection.visibility}
    # collection_return = {"id": collection.id, "name": collection.name, "description": collection.description, "uuid": collection.uuid, "parent_collection_id": collection.parent_collection_id, "date": collection.creation_date, "owner_id": collection.owner_id, "child_collections": [], "child_files": []}
    
    for sc in sub_collections:
        if sc.uuid in list_creds or sc.visibility == "visible" or is_admin(user_id):
            temp_collection = {"id": sc.id, "name": sc.name, "uuid": sc.uuid}
            collection_return["child_collections"].append(temp_collection)
    
    # for file in sub_files:
    #     if file.uuid in list_creds or file.visibility == "visible":
    #         permissions = ["list"]
    #         if file.uuid in read_creds:
    #             permissions.append("read")
    #         if file.uuid in write_creds:
    #             permissions.append("write")
    #         temp_file = {"id": file.id, "name": file.name, "display_name": file.display_name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner_id": file.owner_id, "visibility": file.visibility, "accessibility": file.accessibility, 'collection_id': file.collection_id, 'size': file.size, "permissions": permissions}
    #         collection_return["child_files"].append(temp_file)
    collection_return["path"] = get_parent_collection_path(collection_id)
    return collection_return

def get_collection_files(collection_id, offset, limit, user_id):
    import time
    st = time.time()
    (list_creds, read_creds, write_creds) = get_scope(user_id)
    collection = Collection.query.filter(Collection.id==collection_id).first()
    print(time.time()-st)
    if collection.uuid in list_creds or is_admin(user_id):
        files = []
        sub_files = File.query.filter(File.collection_id==collection_id).order_by(File.id).all()
        for file in sub_files:
            if file.uuid in list_creds or file.visibility == "visible" or is_admin(user_id):
                permissions = ["list"]
                if file.uuid in read_creds:
                    permissions.append("read")
                if file.uuid in write_creds:
                    permissions.append("write")
                temp_file = {"id": file.id, "name": file.name, "display_name": file.display_name, "uuid": file.uuid, "status": file.status, "date": file.creation_date, "owner_id": file.owner_id, "visibility": file.visibility, "accessibility": file.accessibility, 'collection_id': file.collection_id, 'size': file.size, "permissions": permissions}
                files.append(temp_file)
        offset = max(offset, 0)
        limit = min(limit, len(files))
        return {"files": files[offset:(offset+limit)], "total_files": len(files)}
    else:
        return []

def get_parent_collection_path(collection_id):
    collection_path = []
    collection = Collection.query.filter(Collection.id==collection_id).first()
    collection_path.insert(0,{"id": collection.id, "name": collection.name, "description": collection.description, "uuid": collection.uuid})
    while collection.parent_collection_id:
        if len(collection_path) < 30:
            collection = Collection.query.filter(Collection.id==collection.parent_collection_id).first()
            collection_path.insert(0,{"id": collection.id, "name": collection.name, "description": collection.description, "uuid": collection.uuid})
    return collection_path

def update_file(db, file, updater_id):
    db_file = db.session.query(File).filter(File.id == file["id"]).first()
    db_file.display_name = file["display_name"]
    db_file.owner_id = file["owner_id"]
    db_file.collection_id = file["collection_id"]
    db_file.visibility = file["visibility"]
    db_file.status = file["status"]
    db_file.accessibility = file["accessibility"]
    db.session.commit()

def list_policies():
    db_policies = db.session.query(Policy).order_by(Policy.id).all()
    policies = []
    for policy in db_policies:
        policies.append(print_policy(policy))
    return policies

def create_policy(data):
    collections = []
    for collection in data["collections"]:
        db_collection = db.session.query(Collection).filter(Collection.id==collection).first()
        if db_collection is not None:
            collections.append(db_collection)
    files = []
    for file in data["files"]:
        db_file = db.session.query(File).filter(File.id==file).first()
        if db_file is not None:
            files.append(db_file)

    policy = Policy(action=data["action"], effect=data["effect"], collections=collections, files=files)
    db.session.add_all([policy])
    db.session.commit()
    db.session.refresh(policy)
    return(print_policy(policy))

def delete_policy(policy_id):
    dbpolicy = db.session.query(Policy).filter(Policy.id == policy_id).first()
    p = print_policy(dbpolicy)
    Policy.query.filter_by(id=policy_id).delete()
    db.session.commit()
    return(p)

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
    db.session.refresh(akey)
    k = dict(akey.__dict__)
    k.pop('_sa_instance_state', None)
    return  k

def delete_access_key(user_id, key_id):
    if is_admin(user_id) or is_owner_key(user_id, key_id):
        db_access_key = db.session.query(Accesskey).filter(Accesskey.id == key_id).first()
        db.session.delete(db_access_key)
        db.session.commit()
        return 1
    else:
        return 0

def get_key_user(user_key):
    akey = db.session.query(Accesskey).filte(Accesskey.uuid == user_key).first()
    user = db.session.query(User).filter(User.id == akey.owner_id).first()
    return user

def key_valid(user_key):
    try:
        akey = db.session.query(Accesskey).filter(Accesskey.uuid == user_key).first()
        now = datetime.now()
        key_age = (now-akey.creation_date).seconds/60
        if key_age < akey.expiration_time:
            return True
        else:
            return False
    except Exception:
        return False

def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey)) 
            for key, value in obj.__dict__.items() 
            if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj

def validate_json(json_data, schema_data):
    try:
        validate(instance=json_data, schema=schema_data)
    except jsonschema.exceptions.ValidationError as err:
        traceback.print_exc()
        return False
    return True

def filterjson(filter, file, j):
    jkeys = j.keys()
    for k in jkeys:
        if type(j[k]) == int:
            filter = filter.filter(file[k].cast(Integer) == j[k])
        elif type(j[k]) == float:
            filter = filter.filter(file[k].cast(Float) == j[k])
        elif j[k] == None:
            filter = filter.filter(file.has_key(k))
        elif "%" in j[k]:
            filter = filter.filter(file[k].astext.like(j[k]))
        elif type(j[k]) == str:
            filter = filter.filter(file[k].astext == j[k])
        elif "between" in j[k].keys():
            filter = filter.filter(file[k].cast(Float) >= j[k]["between"][0]).filter(file[k].cast(Float) <= j[k]["between"][1])
        else:
            try:
                filter = filterjson(filter, file[k], j[k])
            except Exception:
                traceback.print_exc()
    return filter

def annotate_file(file_id, metadata):
    file = File.query.filter(File.id == file_id).first()
    file.meta = metadata
    db.session.commit()
    db.session.refresh(file)
    file = dict(file.__dict__)
    file.pop('_sa_instance_state', None)
    return(file)

def meta_stat(meta, path, stat):
    for k in meta.keys():
        if str(type(meta[k])) == "<class 'sqlalchemy_json.track.TrackedList'>":
            x=1
        elif str(type(meta[k])) == "<class 'sqlalchemy_json.track.TrackedDict'>":
            stat = meta_stat(meta[k], path+"/"+k, stat)
        else:
            p = path+"/"+k
            metak = meta[k]
            if type(metak) == float:
                metak = str(int(metak))
            if p in stat.keys():
                if str(metak) in stat[p].keys():
                    stat[p][str(metak)] = stat[p][str(metak)]+1
                else:
                    stat[p][str(metak)] = 1
            else:
                temp = {str(metak): 1}
                stat[p] = temp
    return stat

def get_filters(user_id, filter_number_category=20, filter_number_option=10):
    files = File.query.all()
    return collect_meta_stats(files, filter_number_category=filter_number_category, filter_number_option=filter_number_option)

def collect_meta_stats(files, filter_number_category=20, filter_number_option=10):
    stat = {}
    filter_result = []
    for f in files:
        if f.meta != None:
            stat = meta_stat(f.meta, "", stat)
    if filter == 0:
        for s in stat.keys():
            filter_result.append({"category": s, "detail": stat[s]})
    else:
        for s in stat.keys():
            file_count = 0
            temp_stat = {}
            for key in stat[s].keys():
                if stat[s][key] >= filter_number_option:
                    file_count = file_count+stat[s][key]
                    temp_stat[key] = stat[s][key]
            if file_count >= filter_number_category:
                filter_result.append({"category": s, "detail": temp_stat})
    return filter_result

def get_file_metadata(db, file_id, user_id):
    file = db.session.query(File).filter(File.id == file_id).first()
    return file.meta

def get_file_by_id(file_id, user_id):
    #file = File.query.filter(File.id == file_id).first()
    file = db.session.query(File, User, Collection).filter(File.id == file_id).filter(User.id == File.owner_id).filter(Collection.id == File.collection_id).first()
    owner = file[1]
    collection = file[2]
    owner_result = {"first_name": owner.first_name, "last_name": owner.last_name, "id": owner.id, "uuid": owner.uuid}
    collection_result = {"id": collection.id, "name": collection.name, "uuid": collection.uuid}
    file_result = {"id": file[0].id, "name": file[0].name, "display_name": file[0].display_name, "uuid": file[0].uuid, "status": file[0].status, "date": file[0].creation_date, "owner": owner_result, "visibility": file[0].visibility, "accessibility": file[0].accessibility, 'collection': collection_result, 'size': file[0].size, 'meta': file[0].meta}
    return file_result
