# Python standard libraries
from threading import Lock
import sqlite3
import json
import os
import datetime

# Third-party libraries
from flask import Flask, render_template, session, request, redirect, url_for, jsonify
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
from flask_wtf.csrf import CSRFProtect


# Internal imports
from classes import User, CharacterValidation
from db import *





### SET VARIABLES AND INITIALIZE PRIMARY PROCESSES

# Google OAuth configurations
# Visit https://console.developers.google.com/apis/credentials/oauthclient/211539095216-3dnbifedm4u5599jf7spaomla4thoju6.apps.googleusercontent.com?project=seniorproject-294418&supportedpurview=project to get ID and SECRET, then export them in a terminal to set them as environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

session_id = "69BBEG69" #placeholder till we figure out id creation method, use usernames with random numbers?
# TODO: Replace all of the user_key references with the OAuth user_key or user_name
user_key = "BigGamer420" #placeholder till we create some sort of user database?

# This disables the SSL usage check - TODO: solution to this needed as it may pose security risk. see https://oauthlib.readthedocs.io/en/latest/oauth2/security.html and https://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# The GOOGLE_CLIENT_ID and the GOOGLE_CLIENT_SECRET are stored as environment variables. IT IS IMPORTANT THAT THEY ARE NOT STORED ANYWHERE ELSE. Not in this directory, not in this repository, and absolutely not in this file. It is a massive security risk if secret credentials are committed to a public repository.
# To set the GOOGLE_CLIENT_ID and the GOOGLE_CLIENT_SECRET environment variables in a Linux bash terminal, use: `export GOOGLE_CLIENT_ID=your_client_id` and `export GOOGLE_CLIENT_SECRET=your_client_secret`
# Session works on a per-user basis - can't work to store values that multiple users need to access
# Will probably need to store in a database or something
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24) # TODO: What is the best way to get the SECRET_KEY?

socketio = SocketIO(app, async_mode=async_mode)

thread = None
thread_lock = Lock()

# Create the database
create_dbs()

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# CSRF authenticator to prevent CSRF attacks(also flask forms requires...)
csrf = CSRFProtect(app)


### FUNCTIONS

# TODO: move functions to their own .py file to avoid bloating and promote encapsulation
# Retrieves Google's provider configuration
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    db_response = read_db("users", "*", f"WHERE user_id = '{user_id}'")
    if not db_response:
        return None
    return User(id_=db_response[0][0], name=db_response[0][1], email=db_response[0][2], profile_pic=db_response[0][3])

@login_manager.unauthorized_handler
def sent_to_login():
    return redirect(url_for("login_index"))



### ROUTING DIRECTIVES 

# TODO: Refactor all of the character related pages

# Viewing characters page
@app.route("/characters", methods=["GET", "POST"])
@login_required
def view_characters():
    user = read_db("users", "*", f"WHERE user_id = '{current_user.get_user_id()}'")
    if request.method == "POST":
        if request.form['type'] == "delete":
            delete_from_db("characters", f"WHERE user_key = '{user[0][0]}' AND chr_name = '{request.form['character_name']}'")
        elif request.form['type'] == "edit":        # TODO: if user leaves this page before publishing changes, the character is lost
            form = CharacterValidation()
            if form.validate():
                user_id = user[0][0]
                values = (user_id, session_id, form.name.data, form.classname.data, form.subclass.data, form.race.data, form.subrace.data, form.speed.data, form.level.data, form.strength.data, form.dexterity.data, form.constitution.data, form.intelligence.data, form.wisdom.data, form.charisma.data,  form.hitpoints.data)
                print(values)
                add_to_db("chars", values)
            else:
                # TODO: Personalize error messages
                # TODO: Figure out how to pass dropdowns
                err_lis = []
                for errs in form.errors.keys():
                    for mess in form.errors[errs]:
                        err_mes = errs + ": " + mess + "!" +"\n"
                        err_lis += [err_mes]
                whole_err_mes = r''.join(err_lis)
                return render_template("edit_character.html", message_text=whole_err_mes, name=form.name.data, hp=form.hitpoints.data, speed=form.hitpoints.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data)        
    else:
        print("NORMAL")
    items = read_db("characters", "*", f"WHERE user_key = '{user[0][0]}'")
    return render_template("view_characters.html", items=items)


# Character creation page
@app.route("/characters/create", methods=["POST", "GET"])
@login_required
def character_creation():
    form = CharacterValidation()
    if request.method == "POST" and form.validate():
        user = read_db("users", "*", f"WHERE user_id = '{current_user.get_user_id()}'")
        user_id = user[0][0]
        values = (user_id, session_id, form.name.data, form.classname.data, form.subclass.data, form.race.data, form.subrace.data, form.speed.data, form.level.data, form.strength.data, form.dexterity.data, form.constitution.data, form.intelligence.data, form.wisdom.data, form.charisma.data, form.hitpoints.data)
        if read_db("characters", "*", f"WHERE chr_name = '{values[2]}'") != []:
            return render_template("add_character.html", message_text="You already have a character with this name!", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data)
        else:
            print(values)
            add_to_db("chars", values)
            val_char_mess = f""" {values[2]}, the level {values[8]} {values[6]} {values[5]} {values[4]} {values[3]} with 
                        {values[15]} hit points was created by 
                         {current_user.get_name()}!
                                        """
            return render_template("add_character.html", message_text=val_char_mess)
    elif request.method =="POST" and form.errors:
        err_lis = []
        for errs in form.errors.keys():
            for mess in form.errors[errs]:
                err_mes = errs + ": " + mess + "!" +"\n"
                err_lis += [err_mes]
        whole_err_mes = r''.join(err_lis)
        return render_template("add_character.html", message_text=whole_err_mes, name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data)
    return render_template("add_character.html")


@app.route("/characters/edit", methods=["POST"])
@login_required
def edit_character():
    name = request.form['character_name']
    character = read_db("characters", "*", f"WHERE user_id = '{current_user.get_user_id()}' AND chr_name = '{name}'")[0]
    delete_from_db("characters", f"WHERE user_id = '{current_user.get_user_id()}' AND chr_name = '{name}'")
    # TODO: Figure out how to pass the dropdown variables, update as more columns get added
    # TODO: Fix subrace (not supported by db at the moment)
    return render_template("edit_character.html", name=character[2], hp=character[6], old_race=character[5], old_subrace=character[5], old_class=character[3], old_subclass=character[4])


# Post-Login Landing Page
@app.route("/home")
@login_required
def home():
    return render_template("base.html", async_mode=socketio.async_mode)

# TODO: Will want to change how this works
@app.route("/play/choose")
@login_required
def choose_character():
    # TODO: Somehow change the database to update what game the character is in
    user = read_db("users", "*", f"WHERE user_id = '{current_user.get_user_id()}'")
    characters = read_db("characters", "*", f"WHERE user_key = '{user[0][0]}'")
    if characters:
        return render_template("choose_character.html", characters=characters)
    else:
        return render_template("add_character.html", message_text="You need to have a character to join!")


# Gameplay Page
@app.route("/play", methods=["POST"])
@login_required
def play():
    # TODO: Integrate character name into the messages sent by the sockets
    # TODO: Update the database to state that this character is in the game
    return render_template("index.html", async_mode=socketio.async_mode)

# Landing Login Page
@app.route("/")
def login_index():
    if current_user.is_authenticated:
        # TODO: -> need to create way to add information to the DBs via the UI
        # To display current user information, use: current_user.name, current_user.email, current_user.profile_pic
        return redirect(url_for('home'))
    else:
        return render_template("login.html")

# Login Process
@app.route("/login")
def login():
    # Get the authorization endpoint for Google login
    authorization_endpoint = get_google_provider_cfg()["authorization_endpoint"]
    # Use client.prepare_request_uri to build the request to send to Google, and specify the information we want from the user
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

# Login Callback
@app.route("/login/callback")
def callback():
    # Get authorization code Google returns
    code = request.args.get("code")
    # Find out what URL to hit to get access tokens from Google
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens, then parse tokens with the client
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
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Lookup URL provided by Google that has the user information we want 
    uri, headers, body = client.add_token(google_provider_cfg["userinfo_endpoint"])
    userinfo_response = requests.get(uri, headers=headers, data=body)
    # Verify email that Google served us is valid, and verify that the user has authorized us to get their information
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    # Create a user in the datbase if they don't already exist
    user = User(id_=unique_id, name=users_name, email=users_email, profile_pic=picture)
    if not read_db("users", "*", f"WHERE user_id = '{unique_id}'"):
        add_to_db("users", (unique_id, users_name, users_email, picture))
    # Log the user in and send them to the homepage
    login_user(user)
    return redirect(url_for("login_index"))

# Logout
@app.route("/logout")
@login_required   # TODO: customize unauthorized page 
def logout():
    logout_user()
    return redirect(url_for("login_index"))



build_api_db(["race", "class"])

### API ROUTES
@app.route("/api/races")
def get_races():
    races, subraces = get_api_info("race", "race")

    return jsonify(races=list(races), subraces=subraces)

@app.route("/api/classes")
def get_classes():
    classes, subclasses = get_api_info("class", "class")

    return jsonify(classes=list(classes), subclasses=subclasses)





### EVENT HANDLERS

@socketio.on('set_initiative', namespace='/test')
def test_broadcast_message(message):
    # Sends to all connected
    emit('initiative_update', {'data': message['data']}, broadcast=True)
    emit('log_update', {'data': "Initiative Added"}, broadcast=True)
    add_to_db("init", (session_id, user_key, message['data'][0], message['data'][1]))
    s = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    init_name = message['data'][0] + message['data'][1]
    add_to_db("log", (session_id, user_key, "Init", init_name, s) )


@socketio.on('send_chat', namespace='/test')
def test_broadcast_message(message):
    # Sends to all connected
    emit('chat_update', {'data': message['data']}, broadcast=True)
    emit('log_update', {'data': "Chat update"}, broadcast=True)
    s = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    # add_to_db("log", (session_id, user_key, "Chat", message['data'][0], s)) #do we still want to hold chats?
    user_id = user[0][0]
    chr_name = "Yanko"
    add_to_db("chat",(session_id, user_id, char_name, message['data'][0], s))


@socketio.on('connect', namespace='/test')
def test_connect():
    # Sends upon a new connection
    emit('log_update', {'data': "Connected"}, broadcast=True)
    s = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    add_to_db("log", (session_id, user_key, "Connection", "User connected", s))
    init_items = read_db("initiative", "chr_name, init_val")
    # chat_items = read_db("log", "log", "where title = 'Chat'") # Still want this?
    chats = read_db("chat", "user_key, chr_name, chat", f"WHERE room_id = '{session_id}'")
    if init_items != []:
        for item in init_items:
            emit('initiative_update', {'data': item})
        emit('log_update', {'data': "Initiative List Received"})
    if chats != []:
        for item in chats:
            emit('chat_update', {'data': item})
        emit('log_update', {'data': "Chat List Received"})





if __name__ == "__main__":
    app.run(ssl_context="adhoc")





# References
# https://realpython.com/flask-google-login/\
# https://blog.miguelgrinberg.com/post/easy-websockets-with-flask-and-gevent 