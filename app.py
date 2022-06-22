from flask import Flask, url_for, redirect, session, request, jsonify
from authlib.integrations.flask_client import OAuth
import json
from flask_cors import CORS

import traceback

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles, Accesskey

from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)


import requests

import dbutils

import s3utils

from flask import Response

from middleware import login_required, upload_credentials, admin_required, accesskey_login

# dotenv setup
from dotenv import load_dotenv
load_dotenv()

from datetime import timedelta

def read_config():
    f = open('secrets/config.json')
    return json.load(f)

app = Flask(__name__, 
        static_url_path='/st',
        static_folder='static',
        template_folder='templates')

cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = "ffx#xkj$WWs2"
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)

conf = read_config()

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://"+conf["db"]["user"]+":"+conf["db"]["pass"]+"@"+conf["db"]["server"]+":"+conf["db"]["port"]+"/"+conf["db"]["name"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"

db.init_app(app)
migrate = Migrate(app, db)
app.app_context().push()

#oauth config
oauth = OAuth(app)
oauth.register(
    name = "google",
    client_id = conf["web"]["client_id"],
    client_secret = conf["web"]["client_secret"],
    access_token_url = 'https://accounts.google.com/o/oauth2/token',
    access_token_params = None,
    authorize_url = 'https://accounts.google.com/o/oauth2/auth',
    authorize_params = None,
    api_base_url = 'https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint = 'https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)

@app.route('/api/testkey', methods = ["GET"])
@accesskey_login
def test_me():
    return jsonify(message="ok")

# User API endpoints
# - user [GET] -> list all users
# - user [POST]-> create a new user
# - user [PATCH] -> update user
# - user [DELETE] -> delete user
@app.route('/api/user', methods = ["GET"])
@accesskey_login
@login_required
@admin_required
def get_user():
    try:
        users = dbutils.list_users()
        return jsonify(users), 200
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when listing users"), 500

@app.route('/api/user/files', methods = ["GET"])
@accesskey_login
@login_required
def get_user_files():
    try:
        files = dbutils.list_user_files(session["user"]["id"])
        return jsonify(files), 200
    except Exception:
        return jsonify(message="An error occurred when listing users"), 500

@app.route('/api/user', methods = ["POST"])
@accesskey_login
@login_required
@admin_required
def post_user():
    user_info = {
        "name": "Megan Wojciechowicz",
        "first_name": "Megan",
        "last_name": "Wojciechowicz",
        "email": "megan.Wojciechowicz@mssm.edu"
    }
    user = dbutils.create_user(user_info)
    return jsonify(user)

@app.route('/api/user', methods = ["PATCH"])
@accesskey_login
@login_required
@admin_required
def patch_user():
    user = request.get_json()
    try:
        dbutils.update_user(db, user, session["user"]["id"])
        return jsonify(user), 203
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when updating user"), 500

@admin_required
@login_required
@app.route('/api/user', methods = ["DELETE"])
@accesskey_login
def delete_user():
    user = request.get_json()
    try:
        dbutils.delete_user(db, user, session["user"]["id"])
        return jsonify(user), 203
    except Exception:
        return jsonify(message="An error occurred when updating user"), 500
# ------------------- end user -------------------

# File API endpoints
# - file [GET] -> list all files
# - file [POST]-> create a new file
# - file [PATCH] -> update file
# - file [DELETE] -> delete file
@app.route('/api/file', methods = ["GET"])
@accesskey_login
@login_required
@admin_required
def get_file():
    files = dbutils.list_all_files()
    return jsonify(files)

@app.route('/api/file', methods = ["PATCH"])
@accesskey_login
@login_required
@admin_required
def patch_file():
    file = request.get_json()
    print(file["display_name"])
    dbutils.update_file(db, file, session["user"]["id"])
    return jsonify({"done": "ok"})

@app.route('/api/file/<int:file_id>', methods = ["DELETE"])
@accesskey_login
@login_required
def delete_file(file_id):
    print(file_id)
    try:
        user = dict(session).get('user', None)
        res = dbutils.delete_file(file_id, user)
        if res == 1: 
            return jsonify({"action": "file deleted", "file": file_id}), 200
        else:
            return jsonify(message="No permission to delete file"), 500
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when deleting file"), 500
# ------------------- end file -------------------

# Role API endpoints
# - user [GET] -> list all roles
# - user [POST]-> create a new role
# - user [PATCH] -> update role
# - user [DELETE] -> delete role
@app.route('/api/role', methods = ["GET"])
@login_required
@login_required
@admin_required
def get_role():
    roles = dbutils.list_roles()
    return jsonify(roles)

@app.route('/api/role', methods = ["POST"])
def post_role():
    return jsonify({"mode": "POST"})

@app.route('/api/role', methods = ["PATCH"])
def patch_role():
    return jsonify({"mode": "PATCH"})

@app.route('/api/role', methods = ["DELETE"])
def delete_role():
    return jsonify({"mode": "DELETE"})
# ------------------- end role -------------------

# Collection API endpoints
# - user [GET] -> list all roles
# - user [POST]-> create a new role
# - user [PATCH] -> update role
# - user [DELETE] -> delete role
@app.route('/api/collection', methods = ["GET"])
@login_required
@admin_required
def get_collections():
    collections = dbutils.list_collections()
    return jsonify(collections)

@app.route('/api/collection/<int:collection_id>', methods = ["GET"])
@login_required
def get_collection(collection_id):
    user = dict(session).get('user', None)
    collection = dbutils.get_collection(collection_id, user["id"])
    return jsonify(collection)


@app.route('/api/collection', methods = ["POST"])
def post_collection():
    return jsonify({"mode": "POST"})

@app.route('/api/collection', methods = ["PATCH"])
def patch_collection():
    return jsonify({"mode": "PATCH"})

@app.route('/api/collection', methods = ["DELETE"])
def delete_collection():
    return jsonify({"mode": "DELETE"})
# ------------------- end collection -------------------

# Accesskey API endpoints
# - user [GET] -> list all roles
# - user [POST]-> create a new role
# - user [DELETE] -> delete role
@app.route('/api/accesskey', methods = ["GET"])
@accesskey_login
@login_required
def get_access_keys():
    user = dict(session).get('user', None)
    access_keys = dbutils.list_user_access_keys(user["id"])
    return jsonify(access_keys)

@app.route('/api/accesskey/<int:expiration>', methods = ["POST"])
@accesskey_login
@login_required
def post_access_key(expiration):
    user = dict(session).get('user', None)
    dbutils.create_access_key(user["id"], expiration)
    return jsonify({"mode": "POST"})

@app.route('/api/accesskey/<int:akey>', methods = ["DELETE"])
@login_required
def delete_access_key(akey):
    try:
        user = dict(session).get('user', None)
        res = dbutils.delete_access_key(user["id"], akey)
        if res == 1: 
            return jsonify({"action": "key deleted", "key": akey}), 200
        else:
            return jsonify(message="No permission to delete key"), 500
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when deleting key"), 500

# ------------------- end role -------------------

# ------------------ Login/Logout ----------------
@app.route('/login')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/logout')
@accesskey_login
@login_required
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/authorize')
def authorize():
    google = oauth.create_client("google")
    token = google.authorize_access_token()
    response = google.get('userinfo', token=token)
    user = dbutils.get_user(db, response)
    user.admin = dbutils.is_admin(user.id)
    session["user"] = {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "uuid": user.uuid}
    if user.admin:
        session["user"]["admin"] = user.admin
    session.permanent = True
    # do something with the token and profile
    #return redirect('/')
    return redirect('http://localhost:5000/myfiles')

@app.route('/api/i')
@accesskey_login
@login_required
def mycred():
    try:
        return jsonify(session["user"]), 200
    except Exception:
        return jsonify(message="An error occurred when updating user"), 500

# ------------------- end login -------------------


# ------------------ File Download ------------------

@app.route('/api/file/download/<int:fileid>', methods = ['GET'])
@accesskey_login
@login_required
def download(fileid):
    #data = request.get_json()
    db_file = dbutils.get_file(fileid)
    print(db_file)
    response = s3utils.sign_get_file(db_file.uuid+"/"+db_file.name, conf["aws"])
    res = {'status': 'ok', 'response': response}
    return jsonify(res)

# ============== policies ============
@app.route('/api/policies', methods = ['GET'])
@accesskey_login
@login_required
@admin_required
def list_policies():
    policies = dbutils.list_policies()
    return jsonify(policies)

# ============== file upload functions ===============
@app.route('/api/upload', methods = ['POST'])
@accesskey_login
@login_required
@upload_credentials
def upload():
    data = request.get_json()
    db_file = dbutils.create_file(db, data["filename"], data["size"], session["user"]["id"])
    # check whether user has rights to upload data
    # general upload rights, resource write credentials (e.g. user is allowed to write)
    response = s3utils.sign_upload_file(db_file["uuid"]+"/"+data["filename"], conf["aws"])
    res = {'status': 'ok', 'response': response}
    return jsonify(res)

@app.route('/api/startmultipart', methods = ['POST'])
@accesskey_login
@login_required
@upload_credentials
def startmultipart():
    data = request.get_json()
    db_file = dbutils.create_file(db, data["filename"], data["size"], session["user"]["id"])
    response = s3utils.start_multipart(db_file["uuid"]+"/"+data["filename"], conf["aws"])
    res = {'status': 'ok', 'upload_id': response, 'uuid': db_file["uuid"]}
    return jsonify(res)

@app.route('/api/signmultipart', methods = ['POST'])
@accesskey_login
@login_required
@upload_credentials
def signmultipart():
    data = request.get_json()
    url = s3utils.sign_multipart(data["filename"], data["upload_id"], data["part_number"], conf["aws"])
    res = {'status': 'ok', 'url': url}
    return jsonify(res)

@app.route('/api/completemultipart', methods = ['POST'])
@accesskey_login
@login_required
@upload_credentials
def completemultipart():
    data = request.get_json()
    s3utils.complete_multipart(data["filename"], data["upload_id"], data["parts"], conf["aws"])
    res = {'status': 'ok'}
    return jsonify(res)


# ----------- Proxy to next.js frontend -----------

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(*args, **kwargs):
    resp = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, 'http://localhost:3000/'),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response