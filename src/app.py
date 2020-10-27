# Python standard libraries
from threading import Lock
import sqlite3
import json
import os

# Third-party libraries
from flask import Flask, render_template, session, request, redirect, url_for
from flask_socketio import SocketIO, emit 
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user
)
from oauthlib.oauth2 import WebApplicationClient
import requests

# Internal imports
from db import init_db_command
from user import User



# Google OAuth configurations
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
# The GOOGLE_CLIENT_ID and the GOOGLE_CLIENT_SECRET are stored as environment variables. IT IS IMPORTANT THAT THEY ARE NOT STORED ANYWHERE ELSE. Not in this directory, not in this repository, and absolutely not in this file. It is a massive security risk if secret credentials are committed to a public repository.
# To set the GOOGLE_CLIENT_ID and the GOOGLE_CLIENT_SECRET environment variables in a Linux bash terminal, use: `export GOOGLE_CLIENT_ID=your_client_id` and `export GOOGLE_CLIENT_SECRET=your_client_secret`


# Session works on a per-user basis - can't work to store values that multiple users need to access
# Will probably need to store in a database or something
initiative = []
async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24) # TODO: What is the best way to get the SECRET_KEY?
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


def create_db_log(conn):
    cur = conn.cursor()             #saves global ID key, user-specific key, and name of session/battle, DM Name, 
    cur.execute(f""" CREATE TABLE IF NOT EXISTS session_log (
                                        session_id TEXT PRIMARY KEY,
                                        user_key TEXT,
                                        title TEXT,     
                                        log LONGTEXT
                                    ); """)

def create_db_init(conn): #Takes session_id, User_key as main identifiers and then grabs order for the given session
    cur = conn.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS initiative (
                                        session_id TEXT PRIMARY KEY,
                                        User_key TEXT,
                                        order TEXT NOT NULL
                                    ); """)    

def add_to_log(conn, session_id, user_key, title, log):
    cur = conn.cursor()
    print("adding to blog")
    sql = "INSERT INTO log(session_id, user_key, title, log)VALUES(?,?,?,?)"
    item = (session_id, user_key, title, log)
    cur.execute(sql, item)

def add_to_init(conn, session_id, user_key, order):
    cur = conn.cursor()
    sql = "INSERT INTO initiative(session_id, user_key, order)VALUES(?,?,?)"
    item = (session_id, user_key, order)
    cur.execute(sql, item)

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def read_db_init(conn, sesh_id, user_id):
    cur = conn.cursor() 
    init = []
    for row in cur.execute(f"select order from init where session_id = {sesh_id}"):
        init.append(row)
    return init

def read_db_log(conn, sesh_id, user_id):
    cur = conn.cursor() 
    log = []
    for row in cur.execute(f"select log from sesshion_log where session_id = {sesh_id}"):
        log.append(row)
    return log

# Retrieves Google's provider configuration
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()



@app.route("/")
def index():
    conn = create_connection("battle_sesh.db")
    create_db_init(conn)
    create_db_log(conn)
    session_id = "69BBEG69" #placeholder till we figure out id creation method, use usernames with random numbers?
    user_key = "BigGamer420" #placeholder till we create some sort of user database?
    #To Do -> need to create way to add information to the DBs via the UI 
    # add_to_init(session_id, user_key, initiative)
    return render_template("index.html", async_mode=socketio.async_mode)


@socketio.on('set_initiative', namespace='/test')
def test_broadcast_message(message):
    global initiative
    # Sends to all connected
    emit('initiative_update', {'data': message['data']}, broadcast=True)
    initiative += message['data']
    emit('log_update', {'data': "Initiative update"}, broadcast=True)


@socketio.on('send_chat', namespace='/test')
def test_broadcast_message(message):
    # Sends to all connected
    # emit('chat_update', {'data': message['data']}, broadcast=True)
    emit('chat_update', {'data': message['data']}, broadcast=True)
    emit('log_update', {'data': "Chat update"}, broadcast=True)


@socketio.on('connect', namespace='/test')
def test_connect():
    global initiative
    # Sends upon a new connection
    emit('log_update', {'data': "Connected"}, broadcast=True)
    if initiative != []:
        emit('initiative_update', {'data': initiative})
        emit('log_update', {'data': "Initiative update"}, broadcast=True)



# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# Homepage
@app.route("/")
def index():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'


# Login
@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


# Login Callback
@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))



if __name__ == "__main__":
    app.run(ssl_context="adhoc")



# References
# https://realpython.com/flask-google-login/