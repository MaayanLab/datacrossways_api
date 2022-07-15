

from flask import Flask, url_for, redirect, session, request, jsonify, Response
import traceback
import json
import requests

from authlib.integrations.flask_client import OAuth

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from models import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles, Accesskey
import dbutils
import s3utils

from middleware import login_required, upload_credentials, admin_required, accesskey_login

from datetime import timedelta

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

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

db.init_app(app)
#migrate = Migrate(app, db)
app.app_context().push()

#oauth config
oauth = OAuth(app)
oauth.register(
    name = "google",
    client_id = conf["oauth"]["google"]["client_id"],
    client_secret = conf["oauth"]["google"]["client_secret"],
    access_token_url = conf["oauth"]["google"]["token_uri"],
    authorize_url = conf["oauth"]["google"]["auth_uri"],
    api_base_url = 'https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'}
)

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
        return jsonify(users=users), 200
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
    try:
        data = request.get_json()
        user = dbutils.create_user(data)
        return jsonify({"message": "user created successfully", "user": user}), 200
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when creating user"), 500

@app.route('/api/user', methods = ["PATCH"])
@accesskey_login
@login_required
@admin_required
def patch_user():
    try:
        user = request.get_json()
        user = dbutils.update_user(user)
        return jsonify({"message": "user updated", "user": user}), 200
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when updating user"), 500

@accesskey_login
@login_required
@admin_required
@app.route('/api/user/<int:user_id>', methods = ["DELETE"])
def delete_user(user_id):
    user = request.get_json()
    try:
        user = dbutils.delete_user(user_id)
        return jsonify({"message": "user deleted successfully", "user": user}), 203
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when deleting user"), 500
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
    try:
        files = dbutils.list_files()
        return jsonify({"message": "files listed successfully", "files": files})
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when listing files"), 500

@app.route('/api/file', methods = ["POST"])
@accesskey_login
@login_required
@admin_required
def post_file():
    try:
        data = request.get_json()
        db_file = dbutils.create_file(db, data["filename"], data["size"], session["user"]["id"])
        return jsonify(db_file)
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when posting file"), 500

@app.route('/api/file', methods = ["PATCH"])
@accesskey_login
@login_required
@admin_required
def patch_file():
    try:
        file = request.get_json()
        dbutils.update_file(db, file, session["user"]["id"])
        return jsonify(message="file updated"), 200
    except Exception:
        return jsonify(message="An error occurred when updating file"), 500

@app.route('/api/file/<int:file_id>', methods = ["DELETE"])
@accesskey_login
@login_required
def delete_file(file_id):
    try:
        user = dict(session).get('user', None)
        res = dbutils.delete_file(file_id, user)
        if res == 1: 
            return jsonify({"message": "File deleted", "file": file_id}), 200
        else:
            return jsonify(message="No permission to delete file"), 403
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to delete file"), 500

@app.route('/api/file/download/<int:fileid>', methods = ['GET'])
@accesskey_login
@login_required
def download(fileid):
    try:
        user = dict(session).get('user', None)
        if dbutils.is_owner_file(user["id"], fileid) or dbutils.is_admin(user["id"]):
            db_file = dbutils.get_file(fileid)
            print(db_file)
            response = s3utils.sign_get_file(db_file.uuid+"/"+db_file.name, conf["aws"])
            return jsonify({"message": "URL signed", "url": response}), 200
        else:
            return jsonify(message="No permission to download file"), 403
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to sign URL"), 500



# ============== file upload functions ===============
@app.route('/api/file/upload', methods = ['POST'])
@accesskey_login
@login_required
@upload_credentials
def upload():
    try:
        data = request.get_json()
        db_file = dbutils.create_file(db, data["filename"], data["size"], session["user"]["id"])
        # check whether user has rights to upload data
        # general upload rights, resource write credentials (e.g. user is allowed to write)
        response = s3utils.sign_upload_file(db_file["uuid"]+"/"+data["filename"], conf["aws"])
        return jsonify({"message": "URL signed", "url": response, "file": db_file}), 200
    except Exception:
        return jsonify(message="An error occurred when attempting to sign URL"), 500

@app.route('/api/file/startmultipart', methods = ['POST'])
@accesskey_login
@login_required
@upload_credentials
def startmultipart():
    try:
        data = request.get_json()
        db_file = dbutils.create_file(db, data["filename"], data["size"], session["user"]["id"])
        response = s3utils.start_multipart(db_file["uuid"]+"/"+data["filename"], conf["aws"])
        res = {'status': 'ok', 'upload_id': response, 'uuid': db_file["uuid"]}
        return jsonify({"message": "multipart upload started", 'upload_id': response, 'uuid': db_file["uuid"]}), 200
    except Exception: 
        return jsonify(message="An error occurred when attempting to start multipart upload"), 500

@app.route('/api/file/signmultipart', methods = ['POST'])
@accesskey_login
@login_required
@upload_credentials
def signmultipart():
    try:
        data = request.get_json()
        url = s3utils.sign_multipart(data["filename"], data["upload_id"], data["part_number"], conf["aws"])
        return jsonify({'message': 'multipart upload URL signed', 'url': url}), 200 
    except Exception:
        return jsonify(message="An error occurred when attempting to sign multipart upload URL"), 500

@app.route('/api/file/completemultipart', methods = ['POST'])
@accesskey_login
@login_required
@upload_credentials
def completemultipart():
    try:
        data = request.get_json()
        s3utils.complete_multipart(data["filename"], data["upload_id"], data["parts"], conf["aws"])
        return jsonify({'message': 'multipart upload completed'}), 200 
    except Exception:
        return jsonify(message="An error occurred when attempting to complete multipart upload"), 500

# ------------------- end file -------------------

# Role API endpoints
# - user [GET] -> list all roles
# - user [POST]-> create a new role
# - user [PATCH] -> update role
# - user [DELETE] -> delete role
@app.route('/api/role', methods = ["GET"])
@accesskey_login
@login_required
@admin_required
def get_role():
    try:
        roles = dbutils.list_roles()
        return jsonify(roles=roles), 200
    except Exception:
        return jsonify(message="An error occurred when attempting to list roles"), 500

@app.route('/api/role', methods = ["POST"])
def post_role():
    try:
        data = request.get_json()
        pol = []
        if "policies" in data.keys():
            pol = data["policies"]
        role = dbutils.create_role(data["rolename"], policies=pol)
        return jsonify({"message": "role created", "role": role}), 200
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to create role"), 500

@app.route('/api/role', methods = ["PATCH"])
def patch_role():
    try:
        data = request.get_json()
        role = dbutils.update_role(data)
        return jsonify({"message": "role updated", "role": role}), 200
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to update role"), 500


@app.route('/api/role/<int:role_id>', methods = ["DELETE"])
def delete_role(role_id):
    try:
        role = dbutils.delete_role(role_id)
        return jsonify({"message": "role deleted", "role": role}), 200
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to delete role"), 500
        

# ------------------- end role -------------------

# Role API endpoints
# - user [GET] -> list all roles
# - user [POST]-> create a new role
# - user [PATCH] -> update role
# - user [DELETE] -> delete role
@app.route('/api/policy', methods = ["GET"])
@accesskey_login
@login_required
@admin_required
def get_policy():
    try:
        policies = dbutils.list_policies()
        return jsonify(policies=policies), 200
    except Exception:
        return jsonify(message="An error occurred when attempting to list policies"), 500

@app.route('/api/policy', methods = ["POST"])
def post_policy():
    try:
        data = request.get_json()
        policy = dbutils.create_policy(data)
        return jsonify({"message": "policy created", "policy": policy}), 200
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to create policy"), 500

@app.route('/api/policy/<int:policy_id>', methods = ["DELETE"])
def delete_policy(policy_id):
    try:
        policy = dbutils.delete_policy(policy_id)
        return jsonify({"message": "policy deleted", "policy": policy}), 200
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to delete policy"), 500
        


# Collection API endpoints
# - user [GET] -> list all roles
# - user [POST]-> create a new role
# - user [PATCH] -> update role
# - user [DELETE] -> delete role
@app.route('/api/collection', methods = ["GET"])
@login_required
@admin_required
def get_collections():
    try:
        collections = dbutils.list_collections()
        return jsonify({"message": "collections listed successfully", "collections": collections})
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to list collections"), 500

@app.route('/api/collection/<int:collection_id>', methods = ["GET"])
@login_required
def get_collection(collection_id):
    try:
        user = dict(session).get('user', None)
        collections = dbutils.get_collection(collection_id, user["id"])
        return jsonify({"message": "collections listed successfully", "collections": files})
    except Exception:
        traceback.print_exc()


@app.route('/api/collection', methods = ["POST"])
def post_collection():
    try:
        data = request.get_json()
        collection = dbutils.create_collection(data)
        return jsonify({"message": "collections created successfully", "collection": collection})
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to create collection"), 500

@app.route('/api/collection', methods = ["PATCH"])
def patch_collection():
    try:
        data = request.get_json()
        collection = dbutils.update_collection(data)
        return jsonify({"message": "collection updated successfully", "collection": collection})
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to update collection"), 500


@app.route('/api/collection/<int:collection_id>', methods = ["DELETE"])
def delete_collection(collection_id):
    try:
        collection = dbutils.delete_collection(collection_id)
        return jsonify({"message": "collection deleted successfully", "collection": collection})
    except Exception:
        traceback.print_exc()
        return jsonify(message="An error occurred when attempting to delete collection"), 500

# ------------------- end collection -------------------

# Accesskey API endpoints
# - user [GET] -> list all roles
# - user [POST]-> create a new role
# - user [DELETE] -> delete role
@app.route('/api/user/accesskey', methods = ["GET"])
@accesskey_login
@login_required
def get_access_keys():
    user = dict(session).get('user', None)
    access_keys = dbutils.list_user_access_keys(user["id"])
    return jsonify(access_keys)

@app.route('/api/user/accesskey/<int:expiration>', methods = ["POST"])
@accesskey_login
@login_required
def post_access_key(expiration):
    user = dict(session).get('user', None)
    dbutils.create_access_key(user["id"], expiration)
    return jsonify({"mode": "POST"})

@app.route('/api/user/accesskey/<int:akey>', methods = ["DELETE"])
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

@app.route('/api/user/keylogin', methods=["GET"])
def keylogin():
    user = dbutils.get_key_user(user_key)
    session["user"] = {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "uuid": user.uuid}
    session.permanent = True


# ------------------ Login/Logout ----------------
@app.route('/api/user/login')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/api/user/logout')
@accesskey_login
@login_required
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/api/user/authorize')
def authorize():
    google = oauth.create_client("google")
    token = google.authorize_access_token()
    response = google.get('userinfo', token=token)
    print(response.content)
    user = dbutils.get_user(db, response)
    user.admin = dbutils.is_admin(user.id)
    session["user"] = {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "uuid": user.uuid}
    if user.admin:
        session["user"]["admin"] = user.admin
    session.permanent = True
    # do something with the token and profile
    #return redirect('/')
    return redirect(conf["redirect"]["url"]+'/myfiles')

@app.route('/api/user/i')
@accesskey_login
@login_required
def mycred():
    try:
        return jsonify(session["user"]), 200
    except Exception:
        return jsonify(message="An error occurred when updating user"), 500

# ------------------- end login -------------------



# ============== policies ============
@app.route('/api/policies', methods = ['GET'])
@accesskey_login
@login_required
@admin_required
def list_policies():
    policies = dbutils.list_policies()
    return jsonify(policies)

# ----------- Proxy to next.js frontend -----------

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(*args, **kwargs):
    resp = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, conf["frontend"]["url"]),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response