from app import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles

db.drop_all()
db.create_all()

user_1 = User(name='Alexander Lachmann', 
                first_name="Alexander", 
                last_name="Lachmann",
                affiliation="Mount Sinai Hospital",
                email="alexander.lachmann@gmail.com")

root_collection = Collection(name="root", user=user_1)

admin_role = Role(name="admin")
user_1.roles.append(admin_role)

db.session.add(user_1)
db.session.commit()

