from flask import session, jsonify, g
from functools import wraps
import dbutils
from flask import Flask, url_for, redirect, session, request, jsonify
import json

def read_config():
    f = open('secrets/config.json')
    return json.load(f)

conf = read_config()

def dev_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # request.remote_addr is rewritten from X-Forwarded-For by ProxyFix, so
        # a client could claim to be loopback. Use the real TCP peer instead.
        peer = request.environ.get("werkzeug.proxy_fix.orig", {}).get("REMOTE_ADDR", request.remote_addr)
        if conf.get("development", False) is True and peer in {"127.0.0.1", "::1"}:
            user = dbutils.get_dev_login_user()
            if user:
                session["user"] = {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "uuid": user.uuid}
                session.permanent = False
                try:
                    return f(*args, **kwargs)
                finally:
                    session.pop("user", None)
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('user', None)
        if user:
            # A signed cookie outlives the account it was issued for; make sure
            # the user still exists so deleted accounts lose access at once.
            if dbutils.user_exists(user.get("id")):
                return f(*args, **kwargs)
            session.clear()
        return jsonify({'message': 'You are currently not logged in!'}), 401
    return decorated_function

def upload_credentials(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('user', None)
        if dbutils.is_admin(user["id"]) or dbutils.is_uploader(user["id"]):
            return f(*args, **kwargs)
        return jsonify({'message': 'You need to be admin or have permission to upload files.'}), 403
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('user', None)
        if dbutils.is_admin(user["id"]) :
            return f(*args, **kwargs)
        return jsonify({'message': 'You need to be admin for this operation.'}), 403
    return decorated_function

def accesskey_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_key = request.headers.get('x-api-key', None)
        injected_user = False
        if "user" not in session and user_key:
            if not dbutils.key_valid(user_key):
                return jsonify({'message': 'API key invalid or expired.'}), 403
            user = dbutils.get_key_user(user_key)
            if user is None:
                return jsonify({'message': 'API key invalid or expired.'}), 403
            session["user"] = {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "uuid": user.uuid}
            # API keys authenticate only this request. Never mint a renewable
            # browser session whose lifetime can outlive a revoked key.
            session.permanent = False
            injected_user = True
            g.api_key_auth = True
        try:
            return f(*args, **kwargs)
        finally:
            if injected_user:
                session.pop("user", None)
    return decorated_function
