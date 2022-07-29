
import sys
from models import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles
import copy
import random
import json
from sqlalchemy import create_engine

def read_config():
    f = open('secrets/config.json')
    return json.load(f)

conf = read_config()

try:
    dburi = "postgresql://"+conf["db"]["user"]+":"+conf["db"]["pass"]+"@"+conf["db"]["server"]+":"+conf["db"]["port"]+"/"+conf["db"]["name"]
    db = create_engine(url=dburi)
except Exception:
    print("Could not connect to Database")
    quit()

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

uploader_role = Role(name="uploader")

db.session.add_all([user_1, uploader_role])
db.session.commit()
