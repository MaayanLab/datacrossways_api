from flask_sqlalchemy import SQLAlchemy
from pymysql import NULL
import shortuuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_json import mutable_json_type

db = SQLAlchemy()

def generate_uuid(self):
    return str(shortuuid.ShortUUID().random(length=12))

def generate_uuid():
    return str(shortuuid.ShortUUID().random(length=12))

def generate_key(self):
    return str(shortuuid.ShortUUID().random(length=32))

def generate_key():
    return str(shortuuid.ShortUUID().random(length=32))

def default_name(context):
    return context.get_current_parameters()['name']

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String())
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String(), unique=True)
    affiliation = db.Column(db.String())
    creation_date = db.Column(db.DateTime, default=datetime.now)
    uuid = db.Column(db.String(), default=generate_uuid)
    storage_quota = db.Column(db.Integer, default=100000)

    # relationships
    files = db.relationship('File', cascade='all, delete', backref='user', lazy=True)
    collections = db.relationship('Collection', cascade='all, delete', backref='user', lazy=True)
    roles = db.relationship('Role', secondary='user_roles', cascade='all, delete')
    keys = db.relationship('Accesskey', cascade='all, delete', backref='user', lazy=True)

    def __init__(self, name, first_name, last_name, email, affiliation=""):
        self.name = name
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.affiliation = affiliation
    
    def __repr__(self):
        return f"{self.id}-{self.name}-{self.email}-{self.uuid}"
    
    def get_email(self):
        return f"{self.email}"

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class File(db.Model):
    __tablename__ = 'files'
 
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String())
    display_name = db.Column(db.String(), default=default_name)
    uuid = db.Column(db.String(), default=generate_uuid)
    status = db.Column(db.String(), default="uploading")
    visibility = db.Column(db.String(), default="hidden")
    accessibility = db.Column(db.String(), default="locked")
    description = db.Column(db.String())
    creation_date = db.Column(db.DateTime, default=datetime.now)
    size = db.Column(db.Integer(), default=0)
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    collection_id = db.Column(db.Integer(), db.ForeignKey('collections.id'))

    meta = db.Column(mutable_json_type(dbtype=JSONB, nested=True))
    
    def __repr__(self):
        return f"{self.id}: {self.name}: {self.uuid}"
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Collection(db.Model):
    __tablename__ = 'collections'
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String())
    uuid = db.Column(db.String(), default=generate_uuid)
    description = db.Column(db.String())
    image_url = db.Column(db.String(), default="https://datacrosswayspublic.s3.amazonaws.com/collections/collection.jpg")
    creation_date = db.Column(db.DateTime, default=datetime.now)
    parent_collection_id = db.Column(db.Integer(), db.ForeignKey('collections.id'))
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    visibility = db.Column(db.String(), default="hidden")
    accessibility = db.Column(db.String(), default="open")

    # relationships
    collections = db.relationship('Collection', cascade='all, delete', backref=db.backref('parent', remote_side=[id]), lazy=True)
    files = db.relationship('File', cascade='all, delete', backref='collection', lazy=True)
    
    def __repr__(self):
        return f"{self.id}-{self.name}-{self.uuid}"

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Accesskey(db.Model):
    __tablename__ = 'accesskey'
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String())
    uuid = db.Column(db.String(), default=generate_key)
    creation_date = db.Column(db.DateTime, default=datetime.now)
    expiration_time = db.Column(db.Integer, default=1440)
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))


# Define the Role data-model
# Roles have resources and permissions attached to them
# {
#     'id': Integer,
#     'name': String,
#     'permissions': [permission_ids],
#     'resources': [resource_ids]
# }
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(200), unique=True)
    policies = db.relationship('Policy', secondary='role_policy', cascade='all, delete')
    def __repr__(self):
        return f"{self.id}-{self.name}"

class PolicyCollections(db.Model):
    __tablename__ = 'policy_collections'
    id = db.Column(db.Integer(), primary_key=True)
    policy_id = db.Column(db.Integer(), db.ForeignKey('policies.id', ondelete='CASCADE'))
    collection_id = db.Column(db.Integer(), db.ForeignKey('collections.id', ondelete='CASCADE'))

class PolicyFiles(db.Model):
    __tablename__ = 'policy_files'
    id = db.Column(db.Integer(), primary_key=True)
    policy_id = db.Column(db.Integer(), db.ForeignKey('policies.id', ondelete='CASCADE'))
    file_id = db.Column(db.Integer(), db.ForeignKey('files.id', ondelete='CASCADE'))

# Define the UserRoles association table
class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    def __repr__(self):
        return f"{self.id}-{self.user_id}-{self.role_id}"

class RolePolicy(db.Model):
    __tablename__ = 'role_policy'
    id = db.Column(db.Integer(), primary_key=True)
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))
    policy_id = db.Column(db.Integer(), db.ForeignKey('policies.id', ondelete='CASCADE'))

class Policy(db.Model):
    __tablename__ = 'policies'
    id = db.Column(db.Integer(), primary_key=True)

    # should be usually allow, but could be Deny
    effect = db.Column(db.String(10))

    # e.g. list/read/write
    action = db.Column(db.String(100))

    creation_date = db.Column(db.DateTime, default=datetime.now)

    collections = db.relationship('Collection', secondary='policy_collections', cascade='all, delete')
    files = db.relationship('File', secondary='policy_files', cascade='all, delete')
