from flask import Flask, url_for, redirect, session, request, jsonify
from authlib.integrations.flask_client import OAuth
import json
from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, File, Collection, Role, UserRole, Policy, RolePolicy, PolicyCollections, PolicyFiles

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

from middleware import login_required, upload_credentials, admin_required

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


@app.route('/api', methods = ["GET"])
def api():
    return {
        'name': 'Hello World!'
    }

@app.route('/api/createuser', methods = ["GET"])
@login_required
@admin_required
def adduser():
    user_info = {
        "name": "Hans Schnitzel",
        "first_name": "Hansi",
        "last_name": "Schnitzel",
        "email": "hansi@schnitzel.de"
    }
    user = dbutils.create_user(user_info)
    return jsonify(user)

@app.route('/')
@login_required
def hello_world():
    fname= dict(session)["user"]["first_name"]
    result = f'Hello {fname}!'
    result = result+"<hr><br>"+"<a href=\"api/listfiles\">list my files</a>"
    result = result+"<br>"+"<a href=\"api/listusers\">list all users</a>"
    return f'Hello {fname}!'

@app.route('/login')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    google = oauth.create_client("google")
    token = google.authorize_access_token()
    response = google.get('userinfo', token=token)
    user = dbutils.get_user(db, response)
    session["user"] = {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "uuid": user.uuid}
    session.permanent = True
    # do something with the token and profile
    #return redirect('/')
    return redirect('http://localhost:5000/admin')

@app.route('/logout')
@login_required
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/api/updateuser', methods = ['POST'])
@login_required
@admin_required
def update_user():
    user = request.get_json()
    print(user)
    dbutils.update_user(db, user, session["user"]["id"])
    return jsonify(user)

@app.route('/api/updatefile', methods = ['POST'])
@login_required
@admin_required
def update_file():
    file = request.get_json()
    print(file)
    print(file["display_name"])
    dbutils.update_file(db, file, session["user"]["id"])
    #file = dbutils.update_user(db, user, session["user"]["id"])
    return jsonify({"done": "ok"})

@app.route('/api/listfiles', methods = ['GET'])
@login_required
def list_user_files():
    files = dbutils.list_user_files(session["user"]["id"])
    return jsonify(files)

@app.route('/api/listallfiles', methods = ['GET'])
@login_required
@admin_required
def list_all_files():
    files = dbutils.list_all_files()
    return jsonify(files)

@app.route('/api/listusers', methods = ['GET'])
@login_required
@admin_required
def list_users():
    users = dbutils.list_users()
    return jsonify(users)

@app.route('/api/listroles', methods = ['GET'])
@login_required
@admin_required
def list_roles():
    roles = dbutils.list_roles()
    return jsonify(roles)

@app.route('/api/listcollections', methods = ['GET'])
@login_required
@admin_required
def list_collections():
    collections = dbutils.list_collections()
    return jsonify(collections)

@app.route('/api/download', methods = ['POST'])
@login_required
def download():
    #data = request.get_json()
    db_file = dbutils.get_file(12)
    response = s3utils.sign_get_file(db_file.uuid+"/"+db_file.name, conf["aws"])
    res = {'status': 'ok', 'response': response}
    return jsonify(res)

# ============== policies ============
@app.route('/api/policies', methods = ['GET'])
@login_required
@admin_required
def list_policies():
    policies = dbutils.list_policies()
    return jsonify(policies)

# ============== file upload functions ===============
@app.route('/api/upload', methods = ['POST'])
@login_required
@upload_credentials
def upload():
    data = request.get_json()
    db_file = dbutils.create_file(db, data["filename"], session["user"]["id"])
    # check whether user has rights to upload data
    # general upload rights, resource write credentials (e.g. user is allowed to write)
    response = s3utils.sign_upload_file(db_file["uuid"]+"/"+data["filename"], conf["aws"])
    res = {'status': 'ok', 'response': response}
    return jsonify(res)

@app.route('/api/startmultipart', methods = ['POST'])
@login_required
@upload_credentials
def startmultipart():
    data = request.get_json()
    db_file = dbutils.create_file(db, data["filename"], session["user"]["id"])
    response = s3utils.start_multipart(db_file["uuid"]+"/"+data["filename"], conf["aws"])
    res = {'status': 'ok', 'upload_id': response, 'uuid': db_file["uuid"]}
    return jsonify(res)

@app.route('/api/signmultipart', methods = ['POST'])
@login_required
@upload_credentials
def signmultipart():
    data = request.get_json()
    url = s3utils.sign_multipart(data["filename"], data["upload_id"], data["part_number"], conf["aws"])
    res = {'status': 'ok', 'url': url}
    return jsonify(res)

@app.route('/api/completemultipart', methods = ['POST'])
@login_required
@upload_credentials
def completemultipart():
    data = request.get_json()
    s3utils.complete_multipart(data["filename"], data["upload_id"], data["parts"], conf["aws"])
    res = {'status': 'ok'}
    return jsonify(res)

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