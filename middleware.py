from flask import session, jsonify
from functools import wraps
import dbutils
from flask import Flask, url_for, redirect, session, request, jsonify

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
        user_roles = dbutils.get_user_roles(user["id"])
        if "admin" in set(user_roles):
            return f(*args, **kwargs)
        return jsonify({'error': 'You need to be Admin for this operation.'})
    return decorated_function

def accesskey_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_key = request.headers.get('x-api-key', None)
        if user_key:
            user = dbutils.get_key_user(user_key)
            session["user"] = {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "uuid": user.uuid}
            session.permanent = True
            print("user loggd in")
            print(user)
        return f(*args, **kwargs)
    return decorated_function