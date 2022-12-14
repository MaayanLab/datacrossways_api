from app import db, User, Collection, Role
import sys

email= sys.argv[0]
first_name = sys.argv[1]
last_name = sys.argv[2]

db.drop_all()
db.create_all()

user_1 = User(name=first_name+last_name, 
                first_name=first_name, 
                last_name=last_name,
                email=email)

root_collection = Collection(name="root", user=user_1)

admin_role = Role(name="admin")
user_1.roles.append(admin_role)

db.session.add(user_1)
db.session.commit()
