
import sys
from models import User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles
import copy
import random
import json
from sqlalchemy import create_engine
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

conf = json.load(open('secrets/config.json'))

try:
    dburi = "postgresql://"+conf["db"]["user"]+":"+conf["db"]["pass"]+"@"+conf["db"]["server"]+":"+conf["db"]["port"]+"/"+conf["db"]["name"]
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dburi
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
    db.init_app(app)
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

db.session.add(user_1)
db.session.commit()
