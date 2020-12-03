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
from werkzeug.exceptions import HTTPException, BadRequest

# Internal imports
from classes import User, CharacterValidation, RoomValidation
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
    return User(id_=db_response[0][0], name=db_response[0][1], email=db_response[0][2], profile_pic=db_response[0][3], site_name=db_response[0][4])

@login_manager.unauthorized_handler
def sent_to_login():
    return redirect(url_for("login_index"))

def process_character_form(form, user_id, usage):
    if form.validate():
        values = (user_id, session_id, form.name.data, form.classname.data, form.subclass.data, form.race.data, form.subrace.data, form.speed.data, form.level.data, form.strength.data, form.dexterity.data, form.constitution.data, form.intelligence.data, form.wisdom.data, form.charisma.data, form.hitpoints.data)
    
        if usage == "create":
            if read_db("characters", "*", f"WHERE user_key = '{user_id}' AND chr_name = '{values[2]}'") != []:
                app.logger.warning(f"User {current_user.get_site_name()} already has a character with name {form.name.data}. Reloading the Add Character page to allow them to change the name")
                return render_template("add_character.html", message_text="You already have a character with this name!", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

            app.logger.debug(f"User {current_user.get_site_name()} successfully added a character with name {form.name.data}. Redirecting them to the View Characters page.")
            add_to_db("chars", values)
            # char_mess = f""" {values[2]}, the level {values[8]} {values[6]} {values[5]} {values[4]} {values[3]} with 
            #             {values[15]} hit points was created by {current_user.get_site_name()}!"""
            return redirect(url_for("view_characters"))


        elif usage == "edit":
            if request.form['old_name'] != request.form['name'] and read_db("characters", "*", f"WHERE user_key = '{user_id}' AND chr_name = '{request.form['name']}'") != []:
                app.logger.warning(f"User {current_user.get_site_name()} attempted to change the name of character {request.form['old_name']} to {request.form['name']}. They already have another character with that name. Reloading the Edit Character page to allow them to change the name.")
                return render_template("edit_character.html", message_text="You already have a character with this name!", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, old_name=request.form['old_name'], profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

            app.logger.debug(f"Updating the characters owned by user {current_user.get_site_name()}.")
            delete_from_db("characters", f"WHERE user_key = '{user_id}' AND chr_name = '{request.form['old_name']}'")
            add_to_db("chars", values)

            if request.form['old_name'] != form.name.data:
                app.logger.warning(f"User {current_user.get_site_name()} updating the character name. Updating all of the references to that character in the database.")
                update_db("active_room", f"chr_name = '{form.name.data}'", f"WHERE chr_name = '{request.form['old_name']}' AND user_key = '{user_id}'")
                update_db("chat", f"chr_name = '{form.name.data}'", f"WHERE chr_name = '{request.form['old_name']}' AND user_key = '{user_id}'")
            
            app.logger.debug(f"User {current_user.get_site_name()} successfully updated a character with name {form.name.data}. Redirecting them to the View Characters page.")
            return redirect(url_for("view_characters"))
        
        elif usage == "play":
            add_to_db("chars", values)
            app.logger.debug(f"User {current_user.get_site_name()} successfully created their first character with name {form.name.data}. Redirecting them to the Choose Characters Page")
            return redirect(url_for("choose_character"))

    err_lis = []
        
    for errs in form.errors.keys():
        err_mes = errs + ": " + form.errors[errs][0] + "!" +"\n"
        err_lis += [err_mes]

    if usage == "create":
        app.logger.warning(f"Character that user {current_user.get_site_name()} attempted to add had errors. Reloading the Add Character page to allow them to fix the errors.")
        return render_template("add_character.html", errors=err_lis, action="/characters/create", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.charisma.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())
    
    if usage == "edit": 
        app.logger.warning(f"Character that user {current_user.get_site_name()} attempted to edit had errors. Reloading the Edit Character page to allow them to fix the errors.")
        return render_template("edit_character.html", errors=err_lis, name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.charisma.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, old_name=request.form['old_name'], profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

    if usage == "play":
        app.logger.warning(f"Character user {current_user.get_site_name()} attempted to add had errors. Reloading Add Character page to allow them to fix the errors.")
        return render_template("add_character.html", errors=err_lis, action="/play/choose", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.charisma.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

#TODO: Grab token locations
def process_room_form(form, user_id):
    if form.validate():
        values = (user_id, form.room_name.data, "null", "Token Locations",form.map_url.data, form.dm_notes.data)

        app.logger.debug(f"User {current_user.get_site_name()} has created the room called {form.room_name.data}")
        add_to_db("room_object", values)
        return redirect(url_for("home"))

    err_lis = []
        
    for errs in form.errors.keys():
        err_mes = errs + ": " + form.errors[errs][0] + "!" +"\n"
        err_lis += [err_mes]

    return render_template("add_room.html", errors=err_lis)
    

### ROUTING DIRECTIVES 

# Viewing characters page
@app.route("/characters", methods=["GET", "POST"])
@login_required
def view_characters():
    user_id = current_user.get_user_id()

    if request.method == "POST":
        app.logger.debug(f"Attempting to delete character owned by {current_user.get_site_name()} named {request.form['character_name']}.")
        delete_from_db("characters", f"WHERE user_key = '{user_id}' AND chr_name = '{request.form['character_name']}'")
        delete_from_db("active_room", f"WHERE user_key = '{user_id}' AND chr_name = '{request.form['character_name']}'")
                        
    items = read_db("characters", "*", f"WHERE user_key = '{user_id}'")
    app.logger.debug(f"User {current_user.get_site_name()} has gone to view their characters. They have {len(items)} characters.")
    return render_template("view_characters.html", items=items, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())


# Character creation page
@app.route("/characters/create", methods=["POST","GET"])
@login_required
def character_creation():
    form = CharacterValidation()
    user_id = current_user.get_user_id()
    if request.method == "POST":
        app.logger.debug(f"User {current_user.get_site_name()} is attempting to register a character with name {form.name.data}.")
        return process_character_form(form, user_id, "create")

    app.logger.debug(f"User {current_user.get_site_name()} has gone to add a character.")
    return render_template("add_character.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name(), action="/characters/create")


@app.route("/characters/edit/<name>", methods=["GET", "POST"])
@login_required
def edit_character(name):
    user_id = current_user.get_user_id()
    form = CharacterValidation()

    if request.method == "POST":
        app.logger.warning(f"User {current_user.get_site_name()} is attempting to update a character with name {request.form['old_name']}.")
        return process_character_form(form, user_id, "edit")

    character = read_db("characters", "*", f"WHERE user_key = '{current_user.get_user_id()}' AND chr_name = '{name}'")

    if character:
        character = character[0]
        app.logger.debug(f"User {current_user.get_site_name()} has gone to edit a character with name {character[2]}.")
        return render_template("edit_character.html", name=character[2], hp=character[15], old_race=character[5], old_subrace=character[6], old_class=character[3], old_subclass=character[4], speed=character[7], lvl=character[8], str=character[9], dex=character[10], con=character[11], int=character[12], wis=character[13], cha=character[14], old_name=character[2], profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

    app.logger.warning(f"User attempted to edit a character with name {name}. They do not have a character with that name. Throwing a Bad Request error.")
    raise BadRequest(description=f"You don't have a character named {name}!")


# Post-Login Landing Page
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        site_name = request.form["site_name"]
        app.logger.debug(f"User is attempting to set their site name as {site_name}")
        if read_db("users", "*", f"WHERE site_name = '{site_name}'"):
            app.logger.warning(f"Site name {site_name} already has been used. Reloading the Set User Name with warning message.")
            return render_template("set_site_name.html", message="Another user has that username!", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

        app.logger.debug(f"{site_name} is available as a site name. Adding it to the user.")
        update_db("users", f"site_name = '{site_name}'", f"WHERE user_id = '{current_user.get_user_id()}'")
        return redirect(url_for('home'))

    if not current_user.get_site_name():
        app.logger.warning("User does not have site name. Loading the Set User Name page.")
        return render_template("set_site_name.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

    app.logger.debug(f"User {current_user.get_site_name()} has gone to the home page.")

    created_rooms = read_db("room_object", "row_id,room_name,map_url,dm_notes", f"WHERE user_key = {current_user.get_user_id()}")   

    if created_rooms == []:
        created_rooms = [("room/create", "Looks like you don't have any encounters made!", "https://i.pinimg.com/564x/b7/7f/6d/b77f6df018cc374afca057e133fe9814.jpg", "Create rooms to start DMing your own game!")]

    # return render_template("base.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())
    return render_template("home.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name(), room_list=created_rooms)


@app.route("/room/create", methods=["GET", "POST"])
@login_required
def room_creation():
    form = RoomValidation()
    user_id = current_user.get_user_id()

    if request.method == "POST":
        app.logger.debug(f"User {current_user.get_site_name()} is attempting to create a new room named {form.room_name.data}")
        return process_room_form(form, user_id)


    return render_template("add_room.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())


#TODO:Add editability to rooms

# TODO: Will want to change how this works
@app.route("/play/choose", methods=["GET", "POST"])
@login_required
def choose_character():
    # TODO: Update logging stuff when multiple rooms added
    app.logger.debug(f"User {current_user.get_site_name()} has gone to join the singular room.")
    characters = read_db("characters", "*", f"WHERE user_key = '{current_user.get_user_id()}'")
    if characters:
        app.logger.debug(f"User {current_user.get_site_name()} has characters. Loading the Choose Character page.")
        return render_template("choose_character.html", characters=characters, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())
    else:
        user_id = current_user.get_user_id()
        form = CharacterValidation()
        app.logger.warning(f"User {current_user.get_site_name()} does not have characters. Redirecting them to the Add Character page.")
        if request.method == "POST":
            app.logger.debug(f"User {current_user.get_site_name()} is attempting to create their first character.")
            return process_character_form(form, user_id, "play")
        # TODO: Instead of rendering this template at the route "/play/choose", redirect to characters
        return render_template("add_character.html", message_text="You need a character to enter a game!", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name(), action="/play/choose")

# Gameplay Page
@app.route("/play", methods=["POST"])
@login_required
def play():
    # TODO: Check to see if combat has started
    char_name = request.form['character']
    app.logger.debug(f"User {current_user.get_site_name()} has entered the room with character {char_name}.")
    user_id = current_user.get_user_id()
    if not read_db("active_room", extra_clause=f"WHERE room_id = '{session_id}' AND user_key = '{user_id}' AND chr_name = '{char_name}'"):
        add_to_db("active_room", (session_id, user_id, char_name, 0, 0))

    return render_template("play.html", async_mode=socketio.async_mode, char_name=char_name, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

# Landing Login Page
@app.route("/")
def login_index():
    if current_user.is_authenticated:
        app.logger.debug(f"User logged in. Redirecting to the home page")
        return redirect(url_for('home'))
    else:
        app.logger.debug("User not logged in. Loading the login page")
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
    user = User(id_=unique_id, name=users_name, email=users_email, profile_pic=picture, site_name=None)
    if not read_db("users", "*", f"WHERE user_id = '{unique_id}'"):
        add_to_db("users", (unique_id, users_name, users_email, picture, None))
    # Log the user in and send them to the homepage
    login_user(user)
    return redirect(url_for("login_index"))

# Logout
@app.route("/logout")
@login_required
def logout():
    app.logger.debug(f"User {current_user.get_site_name()} just logged out")
    logout_user()
    return redirect(url_for("login_index"))



build_api_db(["race", "class"])

### API ROUTES
# TODO: Hide these behind login requirements or create redirects page and redirect these guys
@app.route("/api/races")
def get_races():
    races, subraces = get_api_info("race", "race")

    return jsonify(races=list(races), subraces=subraces)

@app.route("/api/classes")
def get_classes():
    classes, subclasses = get_api_info("class", "class")

    return jsonify(classes=list(classes), subclasses=subclasses)





### SOCKETIO EVENT HANDLERS

# TODO: Update to work with real room_ids and also update logging messages at that point

@socketio.on('set_initiative', namespace='/combat')
def set_initiative(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    character_name = message['character_name']
    init_val = message['init_val']
    site_name = message['site_name']
    user_id = current_user.get_user_id()
    desc = f"{character_name}'s initiative updated"
    app.logger.debug(f"Battle update: {desc}.")

    if not init_val:
        init_val = read_db("active_room", "init_val", f"WHERE room_id = '{session_id}' AND user_key = '{user_id}' AND chr_name = '{character_name}'")[0][0]

    update_db("active_room", f"init_val = '{init_val}'", f"WHERE room_id = '{session_id}' AND user_key = '{user_id}' AND chr_name = '{character_name}'")
    add_to_db("log", (session_id, user_id, "Init", desc, time_rcvd))

    emit('initiative_update', {'character_name': character_name, 'init_val': init_val, 'site_name': site_name}, broadcast=True)
    emit('log_update', {'desc': desc}, broadcast=True)


@socketio.on('send_chat', namespace='/combat')
def send_chat(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    chr_name = message['character_name']
    app.logger.debug(f"Battle update: {chr_name} has sent chat {message['chat']}.")

    add_to_db("chat",(session_id, user_id, chr_name, message['chat'], time_rcvd))
    add_to_db("log", (session_id, user_id, "Chat", message['character_name'], time_rcvd))

    emit('chat_update', {'chat': message['chat'], 'character_name': message['character_name']}, broadcast=True)


@socketio.on('start_combat', namespace='/combat')
def start_combat(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    characters = read_db("active_room", "user_key, chr_name, init_val", f"WHERE room_id = '{session_id}' ORDER BY init_val, chr_name DESC ")
    first_character = characters[-1]
    app.logger.debug(f"Battle update: Combat has started.")

    update_db("active_room", f"is_turn = '{1}'", f"WHERE room_id = '{session_id}' AND user_key = '{first_character[0]}' AND chr_name = '{first_character[1]}' AND init_val = '{first_character[2]}'")
    add_to_db("log", (session_id, user_id, "Combat", "Started Combat", time_rcvd))

    site_name = read_db("users", "site_name", f"WHERE user_id = '{first_character[0]}'")[0][0]
    emit('combat_started', {'desc': 'Started Combat', 'first_turn_name': first_character[1], 'site_name': site_name}, broadcast=True)


@socketio.on('end_combat', namespace='/combat')
def end_combat(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    character = read_db("active_room","user_key, chr_name", f"WHERE room_id = '{session_id}' AND is_turn = '1'")[0]
    app.logger.debug(f"Battle update: Combat has ended.")

    update_db("active_room", f"is_turn = '{0}'", f"WHERE room_id = '{session_id}'")
    add_to_db("log", (session_id, user_id, "Combat", "Ended Combat", time_rcvd))

    site_name = read_db("users", "site_name", f"WHERE user_id = '{character[0]}'")[0]
    emit('combat_ended', {'desc':'Ended Combat', 'current_turn_name': character[1], 'site_name': site_name}, broadcast=True)


@socketio.on('end_room', namespace='/combat')
def end_session(message):
    delete_from_db("active_room", f"WHERE room_id = '{session_id}'")
    delete_from_db("chat", f"WHERE room_id = '{session_id}'")

    app.logger.debug(f"The room {session_id} owned by {current_user.get_site_name()} has closed")
    
    emit("room_ended", {'desc': message['desc']}, broadcast=True)



@socketio.on('end_turn', namespace='/combat')
def end_turn(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    old_name = message['old_name']
    next_name = message['next_name']
    old_site_name = message['old_site_name']
    next_site_name = message['next_site_name']
    new_character_id = read_db("users", "user_id", f"WHERE site_name = '{next_site_name}'")[0][0]
    app.logger.debug(f"Battle update: {old_name}'s turn has ended. It is now {next_name}'s turn.")

    update_db("active_room", f"is_turn = '{0}'", f"WHERE room_id = '{session_id}'")
    update_db("active_room", f"is_turn = '{1}'", f"WHERE room_id = '{session_id}' AND user_key = '{new_character_id}' AND chr_name = '{next_name}'")
    add_to_db("log", (session_id, user_id, "Combat", f"{old_name}'s Turn Ended", time_rcvd))

    emit("turn_ended", {'desc': message['desc'], 'old_site_name': old_site_name, 'next_site_name': next_site_name}, broadcast=True)


@socketio.on('connect', namespace='/combat')
def connect():
    # Sends upon a new connection
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    site_name = current_user.get_site_name()
    initiatives = read_db("active_room", "chr_name, init_val, user_key", f"WHERE room_id = '{session_id}'")
    chats = read_db("chat", "chr_name, chat", f"WHERE room_id = '{session_id}'")
    app.logger.debug(f"Battle update: User {current_user.get_site_name()} has connected.")

    add_to_db("log", (session_id, user_id, "Connection", f"User with id {user_id} connected", time_rcvd))

    emit('log_update', {'desc': f"{site_name} Connected"}, broadcast=True)

    for item in initiatives:
        site_name = read_db("users", "site_name", f"WHERE user_id = '{item[2]}'")[0][0]
        emit('initiative_update', {'character_name': item[0], 'init_val': item[1], 'site_name': site_name})
    emit('log_update', {'desc': "Initiative List Received"})

    for item in chats:
        emit('chat_update', {'chat': item[1], 'character_name': item[0]})
    emit('log_update', {'desc': "Chat History Received"})


### ERROR HANDLING 

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning(f"A CSRFError has occurred. How did this happen?")
    return render_template("error.html", error_name="Error Code 400" ,error_desc = "The room you were in has closed!", site_name=current_user.get_site_name()), 400

@app.errorhandler(HTTPException)
def generic_error(e):
    # Generic HTTP Exception handler
    app.logger.warning(f"A HTTP error with code {e.code} has occurred. Handling the error.")
    return render_template("error.html", error_name=f"Error Code {e.code}", error_desc=e.description, site_name=current_user.get_site_name(), profile_pic=current_user.get_profile_pic()), e.code


### APP RUNNING
if __name__ == "__main__":
    app.run(ssl_context="adhoc", port=33507, debug=True)

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(logging.DEBUG)
    # app.logger.setLevel(gunicorn_logger.level)

    # app.logger.debug('this is a DEBUG message')
    # app.logger.info('this is an INFO message')
    # app.logger.warning('this is a WARNING message')
    # app.logger.error('this is an ERROR message')
    # app.logger.critical('this is a CRITICAL message')






# References
# https://realpython.com/flask-google-login/\
# https://blog.miguelgrinberg.com/post/easy-websockets-with-flask-and-gevent 
# https://trstringer.com/logging-flask-gunicorn-the-manageable-way/

# heroku specific changes - commit id: 6e0717afc16625b0cddb6410974bdb4c67bbf44f
#	URL: https://github.com/2020SeniorProject/CS-490-Senior-Project/commit/6e0717afc16625b0cddb6410974bdb4c67bbf44f



# TODO: allow characters to sleect who goes first when initiatives tied
# TODO: Hide DM tools from the user view