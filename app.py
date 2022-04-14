from flask import Flask, url_for, redirect, session, request, jsonify
from authlib.integrations.flask_client import OAuth
import json
from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, File, Collection, Role, UserRole
import dbutils

import s3utils

from middleware import login_required, upload_credentials, admin_required

# dotenv setup
from dotenv import load_dotenv
load_dotenv()

from datetime import timedelta

def read_config():
    f = open('secrets/config.json')
    return json.load(f)

app = Flask(__name__, 
        static_url_path='', 
        static_folder='static',
        template_folder='templates')

cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = "ffx#xkj$WWs2"
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

conf = read_config()

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://"+conf["db"]["user"]+":"+conf["db"]["pass"]+"@"+conf["db"]["server"]+":"+conf["db"]["port"]+"/"+conf["db"]["name"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    return redirect('/')

@app.route('/logout')
@login_required
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/api/test', methods = ['GET'])
@login_required
def test():
    print(session["user"])
    file = dbutils.create_file(db, "interface.tsv", session["user"]["id"])
    return jsonify(file)

@app.route('/api/listfiles', methods = ['GET'])
@login_required
def list_user_files():
    files = dbutils.list_user_files(session["user"]["id"])
    return jsonify(files)

@app.route('/api/listusers', methods = ['GET'])
@login_required
@admin_required
def list_users():
    users = dbutils.list_users()
    return jsonify(users)

@app.route('/api/download', methods = ['POST'])
@login_required
def download():
    #data = request.get_json()
    db_file = dbutils.get_file(12)
    response = s3utils.sign_get_file(db_file.uuid+"/"+db_file.name, conf["aws"])
    res = {'status': 'ok', 'response': response}
    return jsonify(res)

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