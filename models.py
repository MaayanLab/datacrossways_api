from flask_sqlalchemy import SQLAlchemy
from pymysql import NULL
import shortuuid
from datetime import datetime

db = SQLAlchemy()

def generate_uuid(self):
    return str(shortuuid.ShortUUID().random(length=12))

def generate_uuid():
    return str(shortuuid.ShortUUID().random(length=12))

def default_name(context):
    return context.get_current_parameters()['name']

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String())
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String())
    affiliation = db.Column(db.String())
    creation_date = db.Column(db.DateTime, default=datetime.now)
    uuid = db.Column(db.String(), default=generate_uuid)

    # relationships
    file_id = db.relationship('File', cascade='all, delete', backref='user', lazy=True)
    collection_id = db.relationship('Collection', cascade='all, delete', backref='user', lazy=True)
    roles = db.relationship('Role', secondary='user_roles')

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
    creation_date = db.Column(db.DateTime, default=datetime.now)
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    collection_id = db.Column(db.Integer(), db.ForeignKey('collections.id'))
    
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
    creation_date = db.Column(db.DateTime, default=datetime.now)
    parent_collection_id = db.Column(db.Integer(), db.ForeignKey('collections.id'))
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    # relationships
    children = db.relationship('Collection', cascade='all, delete', backref=db.backref('parent', remote_side=[id]), lazy=True)
    child_file_id = db.relationship('File', cascade='all, delete', backref='collection', lazy=True)
    #file_id = db.relationship('File', cascade='all, delete', backref='user', lazy=True)

    def __repr__(self):
        return f"{self.id}-{self.name}-{self.uuid}"

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), unique=True)
    #permission = db.Column(db.String(10), unique=True)

    def __repr__(self):
        return f"{self.id}-{self.name}"

# Define the UserRoles association table
class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    def __repr__(self):
        return f"{self.id}-{self.user_id}-{self.role_id}"

# Define the UserRoles association table
class CollectionRole(db.Model):
    __tablename__ = 'collection_roles'
    id = db.Column(db.Integer(), primary_key=True)
    collection_id = db.Column(db.Integer(), db.ForeignKey('collection.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    def __repr__(self):
        return f"{self.id}-{self.collection_id}-{self.role_id}"
