# Python standard libraries
from threading import Lock
import json
import os
import datetime
import logging

# Third-party libraries
from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit 
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient
import requests
from flask_wtf.csrf import CSRFProtect, CSRFError

# Internal imports
from classes import User, CharacterValidation
from db import create_dbs, add_to_db, read_db, delete_from_db, update_db, build_api_db, read_api_db, get_api_info


### SET VARIABLES AND INITIALIZE PRIMARY PROCESSES

# Google OAuth configurations
# Visit https://console.developers.google.com/apis/credentials/oauthclient/211539095216-3dnbifedm4u5599jf7spaomla4thoju6.apps.googleusercontent.com?project=seniorproject-294418&supportedpurview=project to get ID and SECRET, then export them in a terminal to set them as environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

session_id = "69BBEG69" #placeholder till we figure out id creation method, use usernames with random numbers?

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
# 
# below is a link to a walkthrough on how to handle unit testing with socketio and login with flask
# https://blog.miguelgrinberg.com/post/unit-testing-applications-that-use-flask-login-and-flask-socketio
# 
# 
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
    user_id = current_user.get_user_id()

    if request.method == "POST":
        if request.form['type'] == "delete":
            delete_from_db("characters", f"WHERE user_key = '{user_id}' AND chr_name = '{request.form['character_name']}'")
            delete_from_db("room", f"WHERE user_key = '{user_id}' AND chr_name = '{request.form['character_name']}'")

        elif request.form['type'] == "edit":
            form = CharacterValidation()
            if form.validate():
                if request.form['old_name'] != request.form['name'] and read_db("characters", "*", f"WHERE user_key = '{user_id}' AND chr_name = '{request.form['name']}'") != []:
                    return render_template("edit_character.html", message_text="You already have a character with this name!", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, old_name=request.form['old_name'])

                values = (user_id, session_id, form.name.data, form.classname.data, form.subclass.data, form.race.data, form.subrace.data, form.speed.data, form.level.data, form.strength.data, form.dexterity.data, form.constitution.data, form.intelligence.data, form.wisdom.data, form.charisma.data, form.hitpoints.data)

                delete_from_db("characters", f"WHERE user_key = '{user_id}' AND chr_name = '{request.form['old_name']}'")
                add_to_db("chars", values)

            else:
                err_lis = []
                for errs in form.errors.keys():
                    for mess in form.errors[errs]:
                        err_mes = errs + ": " + mess + "!" +"\n"
                        err_lis += [err_mes]

                return render_template("edit_character.html", errors=err_lis, name=form.name.data, hp=form.hitpoints.data, speed=form.hitpoints.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_name=request.form['old_name'])
                        
    items = read_db("characters", "*", f"WHERE user_key = '{user_id}'")
    return render_template("view_characters.html", items=items)


# Character creation page
@app.route("/characters/create", methods=["POST", "GET"])
@login_required
def character_creation():
    form = CharacterValidation()
    if request.method == "POST" and form.validate():
        user_id = current_user.get_user_id()
        values = (user_id, session_id, form.name.data, form.classname.data, form.subclass.data, form.race.data, form.subrace.data, form.speed.data, form.level.data, form.strength.data, form.dexterity.data, form.constitution.data, form.intelligence.data, form.wisdom.data, form.charisma.data, form.hitpoints.data)
        if read_db("characters", "*", f"WHERE user_key = '{user_id}' AND chr_name = '{values[2]}'") != []:
            return render_template("add_character.html", message_text="You already have a character with this name!", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data)
        else:
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
        return render_template("add_character.html", errors=err_lis, name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data)
    return render_template("add_character.html")


@app.route("/characters/edit", methods=["POST"])
@login_required
def edit_character():
    name = request.form['character_name']
    character = read_db("characters", "*", f"WHERE user_key = '{current_user.get_user_id()}' AND chr_name = '{name}'")[0]

    return render_template("edit_character.html", name=character[2], hp=character[15], old_race=character[5], old_subrace=character[6], old_class=character[3], old_subclass=character[4], speed=character[7], lvl=character[8], str=character[9], dex=character[10], con=character[11], int=character[12], wis=character[13], cha=character[14], old_name=character[2])


# Post-Login Landing Page
@app.route("/home")
@login_required
def home():
    return render_template("base.html", async_mode=socketio.async_mode)

# TODO: Will want to change how this works
@app.route("/play/choose")
@login_required
def choose_character():
    user = read_db("users", "*", f"WHERE user_id = '{current_user.get_user_id()}'")
    characters = read_db("characters", "*", f"WHERE user_key = '{user[0][0]}'")
    if characters:
        return render_template("choose_character.html", characters=characters)
    else:
        return render_template("add_character.html", message_text="You need to have a character to join!")

# Gameplay Page
@app.route("/play", methods=["GET", "POST"])
@login_required
def play():
    # TODO: Integrate character name into the messages sent by the sockets
    # TODO: Update the database to state that this character is in the game
    # TODO: Check to see if combat has started
    char_name = request.form['character']
    user_id = current_user.get_user_id()
    if not read_db("room", extra_clause=f"WHERE room_id = '{session_id}' AND user_key = '{user_id}' AND chr_name = '{char_name}'"):
        add_to_db("room", (session_id, user_id, char_name, 0, 0))

    return render_template("play.html", async_mode=socketio.async_mode, char_name=char_name)

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
    # TODO: Truly setup the logger
    # https://trstringer.com/logging-flask-gunicorn-the-manageable-way/
    # It's setup... kinda
    # app.logger.debug('this is a DEBUG message')
    # app.logger.info('this is an INFO message')
    # app.logger.warning('this is a WARNING message')
    # app.logger.error('this is an ERROR message')
    # app.logger.critical('this is a CRITICAL message')

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
@login_required
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





### SOCKETIO EVENT HANDLERS

@socketio.on('set_initiative', namespace='/combat')
def set_initiative(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    character_name = message['character_name']
    init_val = message['init_val']
    user_id = current_user.get_user_id()
    desc = f"{character_name}'s initiative updated"

    update_db("room", f"init_val = '{init_val}'", f"WHERE room_id = '{session_id}' AND user_key = '{user_id}' AND chr_name = '{character_name}'")
    add_to_db("log", (session_id, user_id, "Init", desc, time_rcvd))

    emit('initiative_update', {'character_name': character_name, 'init_val': init_val}, broadcast=True)
    emit('log_update', {'desc': desc}, broadcast=True)


@socketio.on('send_chat', namespace='/combat')
def send_chat(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    chr_name = message['character_name']

    add_to_db("chat",(session_id, user_id, chr_name, message['chat'], time_rcvd))
    add_to_db("log", (session_id, user_id, "Chat", message['character_name'], time_rcvd))

    emit('chat_update', {'chat': message['chat'], 'character_name': message['character_name']}, broadcast=True)


@socketio.on('start_combat', namespace='/combat')
def start_combat(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    characters = read_db("room", "user_key, chr_name, init_val", f"WHERE room_id = '{session_id}' ORDER BY init_val, chr_name DESC ")
    first_character = characters[-1]

    update_db("room", f"is_turn = '{1}'", f"WHERE room_id = '{session_id}' AND user_key = '{first_character[0]}' AND chr_name = '{first_character[1]}' AND init_val = '{first_character[2]}'")
    add_to_db("log", (session_id, user_id, "Combat", "Started Combat", time_rcvd))

    # TODO: Fix to work when the are multiple characters with the same name
    emit('combat_started', {'desc': 'Started Combat', 'first_turn_name': first_character[1]}, broadcast=True)


@socketio.on('end_combat', namespace='/combat')
def end_combat(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    character_name = read_db("room","chr_name", f"WHERE room_id = '{session_id}' AND is_turn = '1'")[0][0]

    update_db("room", f"is_turn = '{0}'", f"WHERE room_id = '{session_id}'")
    add_to_db("log", (session_id, user_id, "Combat", "Ended Combat", time_rcvd))

    emit('combat_ended', {'desc':'Ended Combat', 'current_turn_name': character_name}, broadcast=True)
    # TODO: Should the database be cleared out of the room?


@socketio.on('end_turn', namespace='/combat')
def end_turn(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    old_name = message['old_name']
    next_name = message['next_name']
    new_character_id = read_db("room", "user_key, chr_name", f"WHERE room_id = '{session_id}' AND chr_name = '{next_name}'")[0][0]

    update_db("room", f"is_turn = '{0}'", f"WHERE room_id = '{session_id}'")
    update_db("room", f"is_turn = '{1}'", f"WHERE room_id = '{session_id}' AND user_key = '{new_character_id}' AND chr_name = '{next_name}'")
    add_to_db("log", (session_id, user_id, "Combat", f"{old_name}'s Turn Ended", time_rcvd))

    emit("turn_ended", {'desc': message['desc']}, broadcast=True)


@socketio.on('connect', namespace='/combat')
def connect():
    # Sends upon a new connection
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    user_name = current_user.get_name()
    initiatives = read_db("room", "chr_name, init_val", f"WHERE room_id = '{session_id}'")
    chats = read_db("chat", "chr_name, chat", f"WHERE room_id = '{session_id}'")

    add_to_db("log", (session_id, user_id, "Connection", f"User with id {user_id} connected", time_rcvd))

    emit('log_update', {'desc': f"{user_name} Connected"}, broadcast=True)

    for item in initiatives:
        emit('initiative_update', {'character_name': item[0], 'init_val': item[1]})
    emit('log_update', {'desc': "Initiative List Received"})

    for item in chats:
        emit('chat_update', {'chat': item[1], 'character_name': item[0]})
    emit('log_update', {'desc': "Chat History Received"})


#Error handling

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template("error.html", error_name="Code 400" ,error_desc = "The room you were in has closed!")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error_name="Code 404", error_desc = "This isn't the page you're looking for")

@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", error_name="Code 400", error_desc = "Looks like you missed something!")

# Actual code to run the app
if __name__ == "__main__":
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.run(ssl_context="adhoc", port=33507, debug=True)





# References
# https://realpython.com/flask-google-login/\
# https://blog.miguelgrinberg.com/post/easy-websockets-with-flask-and-gevent 
# heroku specific changes - commit id: 6e0717afc16625b0cddb6410974bdb4c67bbf44f
#	URL: https://github.com/2020SeniorProject/CS-490-Senior-Project/commit/6e0717afc16625b0cddb6410974bdb4c67bbf44f
