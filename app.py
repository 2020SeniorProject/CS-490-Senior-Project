# Python standard libraries
import json
import os
import datetime
import logging
import random
import string

# Third-party libraries
from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, close_room
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient
from requests import get, post
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.exceptions import HTTPException, BadRequest
from apscheduler.schedulers.background import BackgroundScheduler

# Internal imports
from classes import User, CharacterValidation, RoomValidation, SitenameValidation
from db import create_dbs, add_to_db, read_db, delete_from_db, update_db, build_api_db, get_api_info, build_error_db, add_to_error_db, read_error_db


### SET VARIABLES AND INITIALIZE PRIMARY PROCESSES
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
global spam_timeout # in seconds
spam_timeout = 10 
global spam_penalty # in seconds
spam_penalty = 30
global spam_max_messages
spam_max_messages = 5

# Google OAuth configurations
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# This disables the SSL usage check - TODO: solution to this needed as it may pose security risk. see https://oauthlib.readthedocs.io/en/latest/oauth2/security.html and https://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Setups to the SocketIO server that is used
async_mode = None
socketio = SocketIO(app, async_mode=async_mode)

# Create the database
create_dbs()

# Creates the API db
build_api_db(["race", "class"])

# Creates the error holding db
build_error_db()

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# CSRF authenticator to prevent CSRF attacks
csrf = CSRFProtect(app)

# Schedules daily cleaning of DBs (commented out until production)
# scheduler = BackgroundScheduler()
# scheduler.start()

### FUNCTIONS

# Retrieves Google's provider configuration
def get_google_provider_cfg():
    return get(GOOGLE_DISCOVERY_URL).json()

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

def readify_form_errors(form):
    errs_lis = []

    for errs in form.errors.keys():
        err_mes = errs + ": " + form.errors[errs][0] + "!" +"\n"
        errs_lis += [err_mes]

    return errs_lis


def process_character_form(form, user_id, usage, route="/characters/create"):
    if form.validate():
        values = (user_id, form.name.data, form.classname.data, form.subclass.data, form.race.data, form.subrace.data, form.speed.data, form.level.data, form.strength.data, form.dexterity.data, form.constitution.data, form.intelligence.data, form.wisdom.data, form.charisma.data, form.hitpoints.data, form.char_token.data or current_user.get_profile_pic())
    
        if usage == "create":
            if read_db("characters", "*", f"WHERE user_key = '{user_id}' AND chr_name = '{values[1]}'") != []:
                app.logger.warning(f"User {current_user.get_site_name()} already has a character with name {form.name.data}. Reloading the Add Character page to allow them to change the name")
                return render_template("add_character.html", message_text="You already have a character with this name!", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, char_token=form.char_token.data, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

            app.logger.debug(f"User {current_user.get_site_name()} successfully added a character with name {form.name.data}. Redirecting them to the View Characters page.")
            add_to_db("chars", values)

            return redirect(url_for("view_characters"))

        elif usage == "edit":
            if request.form['old_name'] != request.form['name'] and read_db("characters", "*", f"WHERE user_key = '{user_id}' AND chr_name = '{request.form['name']}'") != []:
                app.logger.warning(f"User {current_user.get_site_name()} attempted to change the name of character {request.form['old_name']} to {request.form['name']}. They already have another character with that name. Reloading the Edit Character page to allow them to change the name.")
                return render_template("edit_character.html", message_text="You already have a character with this name!", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, old_name=request.form['old_name'], char_token=form.char_token.data, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

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
            return redirect(route)

    err_lis = readify_form_errors(form)

    if usage == "create":
        app.logger.warning(f"Character that user {current_user.get_site_name()} attempted to add had errors. Reloading the Add Character page to allow them to fix the errors.")
        return render_template("add_character.html", errors=err_lis, action="/characters/create", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.charisma.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data,  char_token=form.char_token.data, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())
    
    if usage == "edit": 
        app.logger.warning(f"Character that user {current_user.get_site_name()} attempted to edit had errors. Reloading the Edit Character page to allow them to fix the errors.")
        return render_template("edit_character.html", errors=err_lis, name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.charisma.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, old_name=request.form['old_name'],  char_token=form.char_token.data, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

    if usage == "play":
        app.logger.warning(f"Character user {current_user.get_site_name()} attempted to add had errors. Reloading Add Character page to allow them to fix the errors.")
        return render_template("add_character.html", errors=err_lis, action="/play/choose", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.charisma.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data,  char_token=form.char_token.data, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())


def process_room_form(form, user_id, usage, room_id):
    if form.validate():
        if usage == "create":

            values = (user_id, form.room_name.data, "null", '{}', form.map_url.data, form.dm_notes.data)
            app.logger.debug(f"User {current_user.get_site_name()} has created the room named {form.room_name.data}")

            add_to_db("room_object", values)
            return redirect(url_for("home"))

        if usage == "edit":

            values = (user_id, form.room_name.data, "null", '{}', form.map_url.data, form.dm_notes.data)
            app.logger.debug(f"User {current_user.get_site_name()} has saved changes to the room named {form.room_name.data}")
            
            delete_from_db("room_object", f"WHERE row_id ='{room_id}'")
            add_to_db("room_object", values)
            return redirect(url_for("home"))

    err_lis = readify_form_errors(form)
    if usage == "create":
        app.logger.debug(f"The room {current_user.get_site_name()} was attempting to create had some errors. Sending back to creation page to fix errors.")
        return render_template("add_room.html", errors=err_lis, room_name=form.room_name.data, map_url=form.map_url.data, dm_notes=form.dm_notes.data ,profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name() )

    if usage == "edit":
        app.logger.debug(f"The room {current_user.get_site_name()} was attempting to edit had some errors. Sending back to edit page to fix errors.")
        return render_template("add_room.html", errors=err_lis, room_name=form.room_name.data, map_url=form.map_url.data, dm_notes=form.dm_notes.data ,profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name() )
        


def determine_if_user_spamming(chats):
    max_messages = spam_max_messages
    timeframe = spam_timeout
    now = datetime.datetime.now()
    total_messages_user_sent= 0
    chats.reverse()
    for message in chats:
        message_time = datetime.datetime.fromisoformat(message[1])
        if ((now - message_time).total_seconds()) < timeframe:
            total_messages_user_sent += 1
        else:
            break
    if total_messages_user_sent > max_messages:
        return True
    return False


def character_icon_add_database(character_name, site_name, character_image, user_id, room_id):
    initial_height = "2em"
    initial_width = "2em"
    initial_top = "25px"
    initial_left = "25px"

    # map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    walla_walla = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    
    # Clean up locally read copy of map_status (or walla_walla in the interm). This is a temporary solution to the larger design problem described at the end of this file. This also fails to preserve character token locations through multiple sessions. Make sure to replace walla_walla with map_status when this is resolved
    wrong_room = []
    for i in walla_walla:
        if walla_walla[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del walla_walla[i]

    json_character_to_add = { user_id: {"site_name": site_name, "character_name": character_name, "room_id": room_id, "character_image": character_image, "height": initial_height, "width": initial_width, "top": initial_top, "left": initial_left}}
    walla_walla[user_id] = json_character_to_add[user_id]
    map_status_json = json.dumps(walla_walla)
    update_db("room_object", f"map_status = '{map_status_json}'", f"WHERE active_room_id = '{room_id}'")

    updated_character_icon_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    emit('redraw_character_tokens_on_map', updated_character_icon_status, room=room_id)


# COMMENTED UNTIL PRODUCTION 
# #Clears Chat, Log, Active rooms 
# def clean_dbs():
#     current_time = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
#     benchmarktime = current_time - datetime.timedelta(hours=24)
#     open_rooms_past_due = read_db("log", "DISTINCT room_id", f"WHERE timestamp > {benchmarktime} ORDER BY timestamp")
#     for room_id in open_rooms_past_due:
#         delete_from_db("active_room", f"WHERE room_id = '{room_id[0]}'")
#         delete_from_db("chat", f"WHERE room_id = '{room_id[0]}'")
#         delete_from_db("log", f"WHERE room_id = '{room_id[0]}'")
#         update_db("room_object", "active_room_id = 'null'", f"WHERE active_room_id = '{room_id[0]}'")

# scheduler.add_job(func=clean_dbs, trigger="cron", hour=3, minute=59)



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
    route = request.args.get('route')
    if request.method == "POST":
        app.logger.debug(f"User {current_user.get_site_name()} is attempting to register a character with name {form.name.data}.")
        if route:
            return process_character_form(form, user_id, "play", route)
            
        return process_character_form(form, user_id, "create")

    app.logger.debug(f"User {current_user.get_site_name()} has gone to add a character.")
    action = "/characters/create"
    if route:
        action += f"?route={route}"
    return render_template("add_character.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name(), action=action)


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
        app.logger.debug(f"User {current_user.get_site_name()} has gone to edit a character with name {character[1]}.")
        return render_template("edit_character.html", name=character[1], hp=character[14], old_race=character[4], old_subrace=character[5], old_class=character[2], old_subclass=character[3], speed=character[6], lvl=character[7], str=character[8], dex=character[9], con=character[10], int=character[11], wis=character[12], cha=character[13], old_name=character[1], char_token=character[15], profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

    app.logger.warning(f"User attempted to edit a character with name {name}. They do not have a character with that name. Throwing a Bad Request error.")
    raise BadRequest(description=f"You don't have a character named {name}!")


# Post-Login Landing Page
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        if "site_name" in request.form:
            site_name = request.form["site_name"]

            form = SitenameValidation()

            if not form.validate():
                err_lis = readify_form_errors(form)
                app.logger.warning(f"There were errors in the chosen site name. Reloading the page")
                return render_template("set_site_name.html", errors=err_lis, error_site_name=site_name, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

            app.logger.debug(f"User is attempting to set their site name as {site_name}")
            if read_db("users", "*", f"WHERE site_name = '{site_name}'"):
                app.logger.warning(f"Site name {site_name} already has been used. Reloading the Set User Name with warning message.")
                return render_template("set_site_name.html", message="Another user has that username!" ,error_site_name=site_name, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

            app.logger.debug(f"{site_name} is available as a site name. Adding it to the user.")
            update_db("users", f"site_name = '{site_name}'", f"WHERE user_id = '{current_user.get_user_id()}'")
            return redirect(url_for('home'))

        if "room_number" in request.form:
            app.logger.debug(f"Attempting to delete room owned by {current_user.get_site_name()} named {request.form['room_name']}.")
            
            if read_db("active_room", "room_id", f"WHERE room_id = {request.form['room_number']}"):
                app.logger.warning(f"User {current_user.get_site_name()} is attempting to delete an active room {request.form['room_name']}")
                # Do we want this responsibility to be on the user or is there merit to just scrubbing the DBs from this page
                return render_template("home.html" , message="Room is active! Close it first!", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name(), room_list=created_rooms)
            
            delete_from_db("room_object", f"WHERE row_id = {request.form['room_number']}")
            app.logger.debug(f"Deleted user {current_user.get_site_name()}'s room {request.form['room_name']}")
            return redirect(url_for('home'))

    if not current_user.get_site_name():
        # site_name is what we call the username in the backend
        app.logger.warning("User does not have site name. Loading the Set User Name page.")
        return render_template("set_site_name.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

    app.logger.debug(f"User {current_user.get_site_name()} has gone to the home page.")

    created_rooms = read_db("room_object", "row_id,room_name,map_url,dm_notes", f"WHERE user_key = '{current_user.get_user_id()}'")   
    if not created_rooms:
        created_rooms = [("create", "Looks like you don't have any encounters made!", "https://i.pinimg.com/564x/b7/7f/6d/b77f6df018cc374afca057e133fe9814.jpg", "Create rooms to start DMing your own game!")]
        default = True
    else:
        default = False

    return render_template("home.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name(), room_list=created_rooms, defaulted = default)


@app.route("/user/settings", methods=["GET", "POST"])
@login_required
def user_settings():
    user_id = current_user.get_user_id()
    characters = read_db("characters", "chr_name, char_token", f"WHERE user_key = '{user_id}'")

    if request.method == "POST":
        if 'site_name' in request.form:
            new_site_name = request.form['site_name']

            form = SitenameValidation()

            if not form.validate():
                err_lis = readify_form_errors(form)
                app.logger.warning(f"There are issues in the renaming form. Allowing the user to change it")
                return render_template("user_settings.html", characters=characters, username_errors=err_lis, new_site_name=new_site_name, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

            if read_db("users", "*", f"WHERE site_name = '{new_site_name}'"):
                app.logger.warning(f"Site name {new_site_name} already has been used. Reloading the user settings page with warning message.")
                return render_template("user_settings.html", characters=characters, username_message="That username is already in use!", new_site_name=new_site_name, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

            app.logger.debug(f"{new_site_name} is available as a site name. Updating {current_user.get_site_name()} site name.")
            update_db("users", f"site_name = '{new_site_name}'", f"WHERE user_id = '{user_id}'")
            return redirect(url_for('user_settings'))
        
        if 'token_url' in request.form:
            new_char_token = request.form['token_url']

            app.logger.debug(f"User's")


    app.logger.debug(f"User {current_user.get_site_name()} is accessing their user settings")
    return render_template("user_settings.html", characters=characters, new_site_name=current_user.get_site_name(), profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())


@app.route("/room/create", methods=["GET", "POST"])
@login_required
def room_creation():
    app.logger.debug(f"User {current_user.get_site_name()} is creating a new room!")
    form = RoomValidation()
    user_id = current_user.get_user_id()

    if request.method == "POST":
        app.logger.debug(f"User {current_user.get_site_name()} is attempting to create a new room")
        return process_room_form(form, user_id, "create", "")

    return render_template("add_room.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name(), map_url="https://i.pinimg.com/564x/b7/7f/6d/b77f6df018cc374afca057e133fe9814.jpg")


@app.route("/room/<room_id>", methods=["GET", "POST"])
@login_required
def room_edit(room_id):
    user_id = current_user.get_user_id()
    form = RoomValidation()

    if request.method == "POST":
        app.logger.warning(f"User {current_user.get_site_name()} is attempting to edit their room")
        return process_room_form(form, user_id, "edit", room_id)

    room = read_db("room_object", "*", f"WHERE rowid = {room_id} and user_key= '{current_user.get_user_id()}'")
    if room:
        room = room[0]
        app.logger.debug(f"User {current_user.get_site_name()} is prepping their room for their encounter!")
        return render_template("edit_room.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name(), map_url= room[5], room_name=room[2], dm_notes = room[6], room_id=room_id )

    app.logger.warning(f"User attempted to prep a room with name {room_id}. They do not have a room with that id. Throwing a Bad Request error.")
    raise BadRequest(description=f"You don't have a room with id: {room_id}!")


@app.route("/generate_room", methods=["POST"])
@login_required
def generate_room_id():
    user_id = current_user.get_user_id()
    room_name = request.form["room_name"]
    random_key = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))

    while read_db("room_object", "*", f"WHERE active_room_id = '{random_key}'"):
        random_key = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))

    update_db("room_object", f"active_room_id = '{random_key}'", f"WHERE user_key = '{user_id}' AND room_name = '{room_name}'")

    return redirect(url_for('enterRoom', room_id=random_key))


@app.route("/play/<room_id>", methods=["GET", "POST"])
@login_required
def enterRoom(room_id):
    user_id = current_user.get_user_id()
    try:
        image_url, map_owner = read_db("room_object", "map_url, user_key", f"WHERE active_room_id = '{room_id}'")[0]
        characters = read_db("characters", "chr_name", f"WHERE user_key='{user_id}'")

        app.logger.debug(f"User {current_user.get_site_name()} has entered the room {room_id}")
        if user_id == map_owner:
            return render_template("play_dm.html", async_mode=socketio.async_mode, characters=characters, in_room=room_id, image_url=image_url, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())
        else:
            return render_template("play.html", async_mode=socketio.async_mode, characters=characters, in_room=room_id, image_url=image_url, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

    except:
        # TODO: Add a pop up on the page to notify user
        app.logger.debug(f"No such room exists")

    # if read_db("active_room", "*", f"WHERE room_id = '{room_id}' AND is_turn = '1'") and not read_db("active_room", "*", f"WHERE room_id = '{room_id}' AND user_key = '{user_id}' AND chr_name = '{char_name}'"):
        # app.logger.debug(f"User {current_user.get_site_name()} is watching the room {room_id}")
        # return render_template("watch.html", async_mode=socketio.async_mode, in_room=room_id, image_url=image_url, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())


# Gameplay Page
@app.route("/play", methods=["GET", "POST"])
@login_required
def play():
    if request.method == "POST":
        room_id = request.form['room_id']

        if read_db("room_object", "*", f"WHERE active_room_id = '{room_id}'"):
            app.logger.debug(f"User {current_user.get_site_name()} is entering room {room_id}")
            return redirect(url_for('enterRoom', room_id=room_id))
        
        app.logger.warning(f"User {current_user.get_site_name()} attempted to enter an nonexistant room. Reloading to form with a message")
        return render_template("choose_room.html", message="There is not an open room with that key!", room_id=room_id, profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())

    app.logger.debug(f"User {current_user.get_site_name()} is attempting to enter a room")
    return render_template("choose_room.html", profile_pic=current_user.get_profile_pic(), site_name=current_user.get_site_name())


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
    token_response = post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Lookup URL provided by Google that has the user information we want 
    uri, headers, body = client.add_token(google_provider_cfg["userinfo_endpoint"])
    userinfo_response = get(uri, headers=headers, data=body)
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


# Delete Account
@app.route("/delete")
@login_required
def delete_account():
    user_id = current_user.get_user_id()
    app.logger.debug(f"User {current_user.get_site_name()} is deleting their account. Deleting all associated information")
    delete_from_db("log", f"WHERE user_key = '{user_id}'")
    delete_from_db("chat", f"WHERE user_key = '{user_id}'")
    delete_from_db("active_room", f"WHERE user_key = '{user_id}'")
    delete_from_db("room_object", f"WHERE user_key = '{user_id}'")
    delete_from_db("users", f"WHERE user_id = '{user_id}'")
    delete_from_db("characters", f"WHERE user_key = '{user_id}'")
    return redirect(url_for("login_index"))




### API ROUTES
@app.route("/api/races")
@login_required
def get_races():
    races, subraces = get_api_info("race", "race")
    return jsonify(races=list(races), subraces=subraces)

@app.route("/api/classes")
@login_required
def get_classes():
    classes, subclasses = get_api_info("class", "class")
    return jsonify(classes=list(classes), subclasses=subclasses)





### SOCKETIO EVENT HANDLERS

@socketio.on('set_initiative', namespace='/combat')
def set_initiative(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    character_name = message['character_name'] or None
    init_val = message['init_val']
    site_name = message['site_name']
    room_id = message['room_id']
    user_id = current_user.get_user_id()

    if not character_name and not init_val:
        return

    desc = f"{character_name}'s initiative updated in room {room_id}"
    app.logger.debug(f"Battle update: {desc}.")

    if not init_val:
        a = read_db("active_room", "init_val", f"WHERE room_id = '{room_id}' AND user_key = '{user_id}' AND chr_name = '{character_name}'")
        init_val = read_db("active_room", "init_val", f"WHERE room_id = '{room_id}' AND user_key = '{user_id}' AND chr_name = '{character_name}'")[0][0]

    update_db("active_room", f"init_val = '{init_val}'", f"WHERE room_id = '{room_id}' AND user_key = '{user_id}' AND chr_name = '{character_name}'")
    add_to_db("log", (room_id, user_id, "Init", desc, time_rcvd))

    emit('initiative_update', {'character_name': character_name, 'init_val': init_val, 'site_name': site_name}, room=room_id)
    emit('log_update', {'desc': desc}, room=room_id)


@socketio.on('send_chat', namespace='/combat')
def send_chat(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    chr_name = message['character_name']
    room_id = message['room_id']
    site_name = current_user.get_site_name()
    app.logger.debug(f"Battle update: {chr_name} has sent chat {message['chat']} in room {room_id}")

    chats = read_db("chat", "user_key, timestamp", f"WHERE room_id = '{room_id}' and user_key = '{user_id}'")

    if determine_if_user_spamming(chats):
        emit("lockout_spammer", {'message': f"Sorry, you can only send {spam_max_messages} messages per {spam_timeout} seconds. Try again in {spam_penalty} seconds.", 'spam_penalty': spam_penalty})
        emit('log_update', {'desc': f"{site_name} was spamming the chat. They have been disabled for {spam_penalty} seconds"}, room=room_id)
        add_to_db("log", (room_id, user_id, "Spam", f"{site_name} was spamming the chat. They have been disabled for {spam_penalty} seconds", time_rcvd))
        app.logger.debug(f"{site_name} was spamming the chat. They have been disabled for {spam_penalty} seconds")


    else:
        add_to_db("chat",(room_id, user_id, chr_name, message['chat'], time_rcvd))
        add_to_db("log", (room_id, user_id, "Chat", message['character_name'], time_rcvd))

        emit('chat_update', {'chat': message['chat'], 'character_name': message['character_name']}, room=room_id)


# TODO: allow characters to select who goes first when initiatives tied
# TODO: Button to hide or show character icon on map
@socketio.on('start_combat', namespace='/combat')
def start_combat(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    room_id = message['room_id']
    characters = read_db("active_room", "user_key, chr_name, init_val", f"WHERE room_id = '{room_id}' ORDER BY init_val, chr_name DESC ")
    first_character = characters[-1]
    app.logger.debug(f"Battle update: Combat has started in room {room_id}")

    update_db("active_room", f"is_turn = '{1}'", f"WHERE room_id = '{room_id}' AND user_key = '{first_character[0]}' AND chr_name = '{first_character[1]}' AND init_val = '{first_character[2]}'")
    add_to_db("log", (room_id, user_id, "Combat", "Started Combat", time_rcvd))

    site_name = read_db("users", "site_name", f"WHERE user_id = '{first_character[0]}'")[0][0]
    emit('combat_started', {'desc': 'Started Combat', 'first_turn_name': first_character[1], 'site_name': site_name}, room=room_id)


@socketio.on('end_combat', namespace='/combat')
def end_combat(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    room_id = message['room_id']
    character = read_db("active_room","user_key, chr_name", f"WHERE room_id = '{room_id}' AND is_turn = '1'")[0]
    app.logger.debug(f"Battle update: Combat has ended in room {room_id}")

    update_db("active_room", f"is_turn = '{0}'", f"WHERE room_id = '{room_id}'")
    add_to_db("log", (room_id, user_id, "Combat", "Ended Combat", time_rcvd))

    site_name = read_db("users", "site_name", f"WHERE user_id = '{character[0]}'")[0]
    emit('combat_ended', {'desc':'Ended Combat', 'current_turn_name': character[1], 'site_name': site_name}, room=room_id)


@socketio.on('end_room', namespace='/combat')
def end_session(message):
    room_id = message['room_id']
    delete_from_db("active_room", f"WHERE room_id = '{room_id}'")
    delete_from_db("chat", f"WHERE room_id = '{room_id}'")
    delete_from_db("log", f"WHERE room_id = '{room_id}'")
    update_db("room_object", "active_room_id = 'null'", f"WHERE active_room_id = '{room_id}'")

    app.logger.debug(f"The room {room_id} owned by {current_user.get_site_name()} has closed")
    
    emit("room_ended", {'desc': message['desc']}, room=room_id)
    close_room(room_id)


@socketio.on('end_turn', namespace='/combat')
def end_turn(message):
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    old_name = message['old_name']
    next_name = message['next_name']
    old_site_name = message['old_site_name']
    next_site_name = message['next_site_name']
    room_id = message['room_id']
    new_character_id = read_db("users", "user_id", f"WHERE site_name = '{next_site_name}'")[0][0]
    app.logger.debug(f"Battle update: {old_name}'s turn has ended. It is now {next_name}'s turn in room {room_id}")

    update_db("active_room", f"is_turn = '{0}'", f"WHERE room_id = '{room_id}'")
    update_db("active_room", f"is_turn = '{1}'", f"WHERE room_id = '{room_id}' AND user_key = '{new_character_id}' AND chr_name = '{next_name}'")
    add_to_db("log", (room_id, user_id, "Combat", f"{old_name}'s Turn Ended", time_rcvd))

    emit("turn_ended", {'desc': message['desc'], 'old_site_name': old_site_name, 'next_site_name': next_site_name}, room=room_id)


@socketio.on('on_join', namespace='/combat')
def on_join(message):
    app.logger.debug(f"Battle update: User {current_user.get_site_name()} has entered room {message['room_id']}")
    join_room(message['room_id'])
    emit('joined', {'desc': 'Joined room'})


@socketio.on('join_actions', namespace='/combat')
def connect(message):
    # Sends upon a new connection
    time_rcvd = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.get_user_id()
    site_name = current_user.get_site_name()
    room_id = message['room_id']
    initiatives = read_db("active_room", "chr_name, init_val, user_key", f"WHERE room_id = '{room_id}'")
    chats = read_db("chat", "chr_name, chat", f"WHERE room_id = '{room_id}'")
    # map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    walla_walla = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    
    # Clean up locally read copy of map_status (or walla_walla in the interm). This is a temporary solution to the larger design problem described at the end of this file. This also fails to preserve character token locations through multiple sessions. Make sure to replace walla_walla with map_status when this is resolved
    wrong_room = []
    for i in walla_walla:
        if walla_walla[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del walla_walla[i]


    add_to_db("log", (room_id, user_id, "Connection", f"User with id {user_id} connected", time_rcvd))
    app.logger.debug(f"Battle update: User {current_user.get_site_name()} has connected to room {room_id}")

    emit('log_update', {'desc': f"{site_name} Connected"}, room=room_id)

    your_chars = []
    character_names_read_from_db = read_db("active_room", "chr_name", f"WHERE user_key='{user_id}' AND room_id='{room_id}'")
    for name in character_names_read_from_db:
        your_chars.append(name[0])
    for player_id in walla_walla:
        if player_id == user_id and walla_walla[player_id]['character_name'] not in your_chars:
            your_chars.append(walla_walla[player_id]['character_name'])
    for char in your_chars:
        emit('populate_select_with_character_names', {'character_name': char, 'site_name': current_user.get_site_name()})

    for item in initiatives:
        site_name = read_db("users", "site_name", f"WHERE user_id = '{item[2]}'")[0][0]
        emit('initiative_update', {'character_name': item[0], 'init_val': item[1], 'site_name': site_name})
    emit('log_update', {'desc': "Initiative List Received"})

    for item in chats:
        emit('chat_update', {'chat': item[1], 'character_name': item[0]})
    emit('log_update', {'desc': "Chat History Received"})

    # populate the map with the character tokens
    if walla_walla:
        emit('redraw_character_tokens_on_map', walla_walla, room=room_id)
        emit('log_update', {'desc': "Character Tokens Received"})

    if read_db("active_room", "*", f"WHERE room_id = '{room_id}' AND is_turn = '1'"):
        emit('log_update', {'desc': "Combat has already started; grabbing the latest information"})

        character = read_db("active_room", "user_key, chr_name", f"WHERE room_id = '{room_id}' AND is_turn = '1'")[0]
        turn_site_name = read_db("users", "site_name", f"WHERE user_id = '{character[0]}'")[0][0]

        emit('combat_connect', {'desc': 'Rejoined Combat', 'first_turn_name': character[1], 'site_name': turn_site_name})


@socketio.on('character_icon_update_database', namespace='/combat')
def character_icon_update_database(message):
    site_name = message['site_name']
    room_id = message['room_id']
    temp_read_for_user_id = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    for character in temp_read_for_user_id:
        if temp_read_for_user_id[character]['site_name'] == message['site_name'] and temp_read_for_user_id[character]['character_name'] == message['character_name']:
            print(character)
            user_id = character
    
    # map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    walla_walla = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    
    # Clean up locally read copy of map_status (or walla_walla in the interm). This is a temporary solution to the larger design problem described at the end of this file. This also fails to preserve character token locations through multiple sessions. Make sure to replace walla_walla with map_status when this is resolved
    wrong_room = []
    for i in walla_walla:
        if walla_walla[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del walla_walla[i]

    # Ensure that there is a valid value for the token position and size
    if message['new_top'] == "Null":
        new_top = walla_walla[user_id]['top']
    else:
        new_top = message['new_top']
    if message['new_left'] == "Null":
        new_left = walla_walla[user_id]['left']
    else:
        new_left = message['new_left']
    if message['new_width'] == "Null":
        new_width = walla_walla[user_id]['width']
    else:
        new_width = message['new_width']
    if message['new_height'] == "Null":
        new_height = walla_walla[user_id]['height']
    else:
        new_height = message['new_height']
        

    # TODO: Add check here to make sure that the token you're trying to move is your own and not someone elses. Check the user_id from user_id = character in the loop above against current_user.get_site_name(). Add exception for if you are the DM
    json_character_to_update = { user_id: {"site_name": message['site_name'], "character_name": message['character_name'], "room_id": message['room_id'], "character_image": message['character_image'], "height": new_height, "width": new_width, "top": new_top, "left": new_left}}
    walla_walla[user_id] = json_character_to_update[user_id]
    characters_json = json.dumps(walla_walla)
    update_db("room_object", f"map_status = '{characters_json}'", f"WHERE active_room_id = '{room_id}'")

    if message['desc'] == "Resize":
        app.logger.debug(f"User {site_name} has resized their character")
    elif message['desc'] == "ChangeLocation":
        app.logger.debug(f"User {site_name} has moved their character to X:{message['new_left']}, Y:{message['new_top']}")
        emit('log_update', {'desc': f"{message['character_name']} moved"})

    emit('redraw_character_tokens_on_map', walla_walla, room=room_id)


@socketio.on('add_character', namespace='/combat')
def add_character(message):
    character_name = message['char_name']
    room_id = message['room_id']
    user_id = current_user.get_user_id()
    site_name = message['site_name']
    temp_db_read_character_token = read_db("characters", "char_token", f"WHERE user_key = '{user_id}' AND chr_name = '{character_name}'")
    init_val = 0

    if temp_db_read_character_token:
        character_image = temp_db_read_character_token[0][0]
    else:
        # TODO: This is just a place holder for if a user does not have an image for their character - but that should never happen anyways
        character_image = "http://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Auto_Racing_Black_Box.svg/800px-Auto_Racing_Black_Box.svg.png"

    temp_db_read_init_value = read_db("active_room", "init_val", f"WHERE room_id='{room_id}' AND user_key = '{user_id}' AND chr_name = '{character_name}'")
    if temp_db_read_init_value:
        init_val = temp_db_read_init_value[0][0]
    else:
        add_to_db("active_room", (room_id, user_id, character_name, 0, 0, character_image))

    emit('populate_select_with_character_names', {'character_name': character_name, 'site_name': site_name}, room=room_id)
    emit('initiative_update', {'character_name': character_name, 'init_val': init_val, 'site_name': site_name}, room=room_id)
    character_icon_add_database(character_name, site_name, character_image, user_id, room_id)
    app.logger.debug(f"User {site_name} has added character {character_name} to the battle")



### ERROR HANDLING 

# @app.errorhandler(CSRFError)
# def handle_csrf_error(e):
#     app.logger.warning(f"A CSRFError has occurred. How did this happen?")
#     return render_template("error.html", error_name="Error Code 400" ,error_desc = "The room you were in has closed!", site_name=current_user.get_site_name()), 400

# @app.errorhandler(HTTPException)
# def generic_error(e):
#     # Generic HTTP Exception handler
#         app.logger.warning(f"A HTTP error with code {e.code} has occurred. Handling the error.")
#         return render_template("error.html", error_name=f"Error Code {e.code}", error_desc=e.description, site_name=current_user.get_site_name(), profile_pic=current_user.get_profile_pic()), e.code

# @app.errorhandler(Exception)
# def five_hundred_error(e):
#     app.logger.warning(f"A server error occurred. Handling it, but you probably should fix the bug...")
#     app.logger.error(f"Here it is: {e}")
#     desc = "Internal Server Error. Congrats! You found an unexpected feature! Care to tell us about it?"
#     return render_template("error.html", error_name="Error Code 500", error_desc=desc, site_name=current_user.get_site_name(), profile_pic=current_user.get_profile_pic()), 500

# @app.route("/process_error", methods=["POST"])
# @login_required
# def process_error():
#     if 'error_desc' in request.form:
#         add_to_error_db(request.form['error_desc'])
    
#     return redirect(url_for("home"))



### APP RUNNING
if __name__ == "__main__":
    app.run(ssl_context="adhoc", port=33507, debug=True)

if __name__ != "__main__":
    # logging levels: info, debug, warning, critical, error
    
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(logging.DEBUG)
    # app.logger.setLevel(gunicorn_logger.level)


# References
# https://realpython.com/flask-google-login/\
# https://blog.miguelgrinberg.com/post/easy-websockets-with-flask-and-gevent 
# https://trstringer.com/logging-flask-gunicorn-the-manageable-way/
# https://flask-login.readthedocs.io/en/latest
# https://stackoverflow.com/a/30779367

# Developer Links
# Visit https://console.developers.google.com/apis/credentials/oauthclient/211539095216-3dnbifedm4u5599jf7spaomla4thoju6.apps.googleusercontent.com?project=seniorproject-294418&supportedpurview=project to get ID and SECRET, then export them in a terminal to set them as environment variables

# Heroku specific changes - commit id: 6e0717afc16625b0cddb6410974bdb4c67bbf44f
#	URL: https://github.com/2020SeniorProject/CS-490-Senior-Project/commit/6e0717afc16625b0cddb6410974bdb4c67bbf44f

### Commit specific resources:
# http://jsfiddle.net/jcgbq46p/19/
# https://api.jqueryui.com/droppable/#event-drop
# https://learn.jquery.com/jquery-ui/getting-started/
# http://jsfiddle.net/8wkj2z79/1/
# http://jsfiddle.net/v6PME/1/
# https://stackoverflow.com/questions/22268881/referenceerror-is-not-defined/22268906
# https://learn.jquery.com/using-jquery-core/document-ready/
# https://www.w3schools.com/cssref/css_selectors.asp

# TODO: Prevent chat spam!
# TODO: When DMs upload battle maps, have the option to specify how many squares wide and how many tall, then have selectors for character tokens for different sizes, and have character tokens snap into the grid
# TODO: Rename script.js
# TODO: change current_user.get_site_name() to current_user.get_username() or something of the like. get_site_name() is confusing
# TODO: Check if a user is already logged in a different window when they attempt to login
# TODO: rename variable 'site_name' to something like 'user_site_name' because site_name is confusing
# TODO: Get stuff from MTF and mythic oddessy of pharoes
# TODO: The check to ensure that a user has a character before joining a room is not working
# TODO: add check to ensure that a user submits an image along with their character at time of creation. Cannot be nothing
# TODO: rename variable "character_image" to "character_token_image"
# TODO: disable start battle button if no characters in initiative
# TODO: Fix sending chats when you have no character in the room displaying as coming from "Add a character first"
# TODO: add a check to make sure that a user submits a character image with their character
# TODO: add a UI option in /play to allow a user to remove their character from the init order
# TODO: Include list of users already in the room in initial log message when joining room



# Issue discovery. What do to about active_room table and room_object table. What information should be stored in each, respectively? 
# when a user hops into join_actions, they are supposed to have their map and their initiative order updated. Init order gets updated just fine
# because the program reads from active_room table, so if no characters have been added to the battle map yet, nothing is in the active_room
# table for initiatives. However, map_status reads from room_object table and that means that if a hops into join_actions and no characters
# have been added yet, they will still see their character tokens appear on the map. I think that we should sync initiative order with
# map_status, probably by moving both to room_object. What's the harm in preserving initiative order in that table?

# I have a work around for the problem above, I will double check that the room id for each character token in map_status matches the current room_id token, but this is just a temporary fix. If this design problem is not solved, map_status could easily balloon into a very large bit of data