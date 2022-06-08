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


from app import db, User, File, Collection, Role, UserRole
user = db.session.query(User).filter(User.id == 1).first()
user.affiliation = "Mount Sinai"
db.session.commit()

user = db.session.query(User).filter(User.id == 1).first()
print(user.affiliation)


db_user = db.session.query(User).filter(User.id == 1).first()

user = {}
user["roles"] = {"Admin": True, "ListFiles": False, "Uploader": False}

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



from app import db, User, File, Collection, Role, UserRole
db.session.query(
    File, 
    User.name
).filter(
    File.owner_id == User.id
).all()

from app import db, User, File, Collection, Role, UserRole
db.session.query(File, User.name).filter(File.owner_id == User.id).all()[0]



from app import db, User, File, Collection, Role, UserRole
collection = Collection(name="base", user=user_1)
db.session.add_all([collection])
db.session.commit()

from app import db, User, File, Collection, Role, UserRole

base = Collection.query.filter(Collection.id == 1).first()
user = User.query.filter(User.id == 3).first()
collection = Collection(name="lymedata2", user=user, collection=base)


db.session.add_all([collection])
db.session.commit()


from app import db, User, File, Collection, Role, UserRole
base = Collection.query.filter(Collection.parent_collection_id == 1).first()
print(base)

base = Collection.query.filter(Collection.parent_collection_id == 2).first()
print(base)

# ========== roles=============
from app import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles

db.drop_all()
db.create_all()

user = User(name='Alexander Lachmann', 
                first_name="Alexander", 
                last_name="Lachmann",
                affiliation="Mount Sinai Hospital",
                email="test@test.com")

base_col = Collection(name="root", user=user)
file = File(name="file.txt", user=user, collection=base_col)
db.session.add_all([file])
db.session.commit()

policy = Policy(effect="allow", action="read")
policy.collections.append(base_col)

policy = Policy(effect="allow", action="admin")

role = Role(name="base reader")
role.policies.append(policy)

user.roles.append(role)

#db.session.add_all([policy, role])
db.session.commit()


from app import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles

uploader_role = Role(name="upload")
db.session.add_all([uploader_role])
db.session.commit()



# create a key for user 1


from app import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles, Accesskey

db_user = db.session.query(User).filter(User.id == 1).first()
akey = Accesskey(name="adminkey", user=db_user)

db.session.commit()

k = Accesskey.query.filter(Accesskey.id == 1).first()
k.owner_id


from app import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles, Accesskey

userid = 3

import time


t = time.time()
res = db.session.query(User, Policy, Role, UserRole, RolePolicy, PolicyCollections, Collection).all()
print(time.time()-t)

from sqlalchemy.orm import joinedload

t = time.time()
res = db.session.query(User).options(
    joinedload(User.collection_id).
    subqueryload(Collection.child_file_id)).all()
print(time.time()-t)

t = time.time()
res = db.session.query(User).options(
    joinedload(User.collection_id).
    subqueryload(Collection.child_file_id)).all()
print(time.time()-t)


t = time.time()
res = db.session.query(User, Policy, Role, UserRole, RolePolicy, PolicyCollections, Collection).filter(User.id == userid).filter(UserRole.user_id == userid).filter(UserRole.role_id == Role.id).filter(Role.id == RolePolicy.role_id).filter(Policy.id == RolePolicy.policy_id).filter(PolicyCollections.policy_id == Policy.id).filter(Collection.id == PolicyCollections.collection_id).all()
print(time.time()-t)

for u, p, r, ur, rp, pc, c in res:
    print(c.name+" - "+p.action)

db.session.query(User, UserRole, Role).filter(User.id == UserRole.user_id).filter(Role.id == UserRole.role_id).filter(User.id == userid).all()

db.session.query(User).filter(User.id == userid).join(UserRole, User.id == UserRole.user_id).all()
