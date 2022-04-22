from app import db, User, File, Collection, Role, UserRole

db.drop_all()
db.create_all()

user_1 = User(name='Alexander Lachmann', 
                first_name="Alexander", 
                last_name="Lachmann",
                affiliation="Mount Sinai Hospital",
                email="test@test.com")

user_1.roles.append(Role(name="Admin"))
#db.session.commit()

user_2 = User(name='Yon Lachmann', 
                first_name="Yon", 
                last_name="Lachmann",
                affiliation="Columbia University",
                email="test@test2.com")

#user_2.roles.append(admin_role)
user_2.roles.append(Role(name="ListFiles"))
user_2.roles.append(Role(name="Uploader"))

file_1 = File(name="file_1.txt", user=user_1)
file_2 = File(name="file_2.txt", user=user_1)
file_3 = File(name="file_3.txt", user=user_1)

file_4 = File(name="file_4.txt", user=user_2)
file_5 = File(name="file_5.txt", user=user_2)

#file_6 = File(name="file_6.txt", user=user_3)
#file_7 = File(name="file_7.txt", user=user_3)

db.session.add_all([file_1, file_2, file_3, file_4, file_5])
db.session.commit()


admin_role = Role.query.filter(Role.name=="Admin").first()

user_3 = User(name='Alexander Lachmann2', 
                first_name="Alexander2", 
                last_name="Lachmann2",
                affiliation="Mount Sinai Hospital",
                email="alexander.lachmann@gmail.com")

user_3.roles.append(admin_role)

db.session.add_all([user_3])

db.session.commit()

# user_id = 3
# role_name = "Admin"
# user = db.session.query(User).filter(User.id == user_id).first()
# user.roles.append(admin_role)
# db.session.commit()
