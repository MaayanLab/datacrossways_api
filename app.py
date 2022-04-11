from flask import Flask, url_for, redirect, session, request, jsonify
from authlib.integrations.flask_client import OAuth
import json
from flask_cors import CORS

import s3utils

from auth_decorator import login_required

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

@app.route('/')
@login_required
def hello_world():
    email= dict(session).get("email", None)
    return f'Hello {email}!'

@app.route('/login')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    google = oauth.create_client("google")
    token = google.authorize_access_token()
    resp = google.get('userinfo', token=token)
    user_info = resp.json()
    session["profile"] = user_info
    session.permanent = True
    # do something with the token and profile
    return redirect('/')

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/upload', methods = ['POST'])
def upload():
    data = request.get_json()
    # check whether user has rights to upload data
    # general upload rights, resource write credentials (e.g. user is allowed to write)
    response = s3utils.sign_upload_file(data["filename"], conf["aws"])
    res = {'status': 'ok', 'response': response}
    return jsonify(res)

@app.route('/startmultipart', methods = ['POST'])
def startmultipart():
    data = request.get_json()
    response = s3utils.start_multipart(data["filename"], conf["aws"])
    res = {'status': 'ok', 'upload_id': response}
    return jsonify(res)

@app.route('/signmultipart', methods = ['POST'])
def signmultipart():
    data = request.get_json()
    url = s3utils.sign_multipart(data["filename"], data["upload_id"], data["part_number"], conf["aws"])
    res = {'status': 'ok', 'url': url}
    return jsonify(res)

@app.route('/completemultipart', methods = ['POST'])
def completemultipart():
    data = request.get_json()
    print(data)
    s3utils.complete_multipart(data["filename"], data["upload_id"], data["parts"], conf["aws"])
    res = {'status': 'ok'}
    return jsonify(res)