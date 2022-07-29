
import sys
from models import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles
import copy
import random
import json

def read_config():
    f = open('secrets/config.json')
    return json.load(f)

conf = read_config()

dburi = "postgresql://"+conf["db"]["user"]+":"+conf["db"]["pass"]+"@"+conf["db"]["server"]+":"+conf["db"]["port"]+"/"+conf["db"]["name"]

print(dburi)

