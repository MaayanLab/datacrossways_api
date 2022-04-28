from flask import session, jsonify
from functools import wraps
import dbutils

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('user', None)
        # You would add a check here and usethe user id or something to fetch
        # the other data for that user/check if they exist
        if user:
            return f(*args, **kwargs)
        return jsonify({'error': 'You are currently not logged in!'})
    return decorated_function

def upload_credentials(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('user', None)
        # You would add a check here and usethe user id or something to fetch
        # the other data for that user/check if they exist
        if user:
            return f(*args, **kwargs)
        return 'You are currently not allowed to upload data. Ask an administrator for help.'
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('user', None)
        print(user)
        user_roles = dbutils.get_user_roles(user["id"])
        print(user_roles)
        if "admin" in set(user_roles):
            return f(*args, **kwargs)
        return jsonify({'error': 'You need to be Admin for this operation.'})
    return decorated_function