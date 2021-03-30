"""
Imported Libraries:
    This is a list of all imported libraries. 
    
    They are organized as follows in alphabetical order:
        1. Python standard libraries
        2. Third-party libaries
        3. Internal imports
"""

# Python standard libraries
import datetime
import json
import logging
import os
import random
import string

# Third-party libraries
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, LoginManager, logout_user
from flask_socketio import close_room, emit, join_room, SocketIO
from flask_wtf.csrf import CSRFError, CSRFProtect
from oauthlib.oauth2 import WebApplicationClient
from requests import get, post
from werkzeug.exceptions import BadRequest, HTTPException

# Internal imports
from classes import AnonymousUser, CharacterValidation, RoomValidation, User, UsernameValidation
from db import add_to_db, add_to_error_db, build_api_db, build_error_db, create_dbs, delete_from_db, get_api_info, read_db, read_error_db, update_db


"""
Initialization and Setup:
    All of these function calls and variable
    definitions are used in the initialization
    of the application. 
    
    It is organized as follows:
        1.  Flask application initialization and
            variable setting
        2.  SocketIO application initialization and
            variable setting
        3.  Flask Login manager initiazation and variable
            setting
        4.  CSRF protection
        5.  Serverside Google OAuth initialization and 
            configuation
        6.  Google Oath client handler initialization
        7.  Database creation
        8.  Scheduled database clearing
        9.  Chat spam limits
        10. NPC setup
"""
# TODO: Should we have a "setup" function?
# Basic Flask application
app = Flask(__name__)
# TODO: hmmmm... this doesn't seem like it's good
app.config['SECRET_KEY'] = 'secret!'
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Setups to the SocketIO server that is used
# None defaults to whatever supported library is installed
async_mode = None
socketio = SocketIO(app, async_mode=async_mode)

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = AnonymousUser

# CSRF authenticator to prevent CSRF attacks
csrf = CSRFProtect(app)

# Google OAuth configurations
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
# This disables the SSL usage check - TODO: solution to this needed as it may pose security risk. see https://oauthlib.readthedocs.io/en/latest/oauth2/security.html and https://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Database creation
create_dbs()
build_api_db(["race", "class"])
build_error_db()

# Schedules cleaning (every 4 hours) of DBs
scheduler = BackgroundScheduler()
scheduler.start()

# Global variables for chats
spam_timeout = 10 
spam_penalty = 30
spam_max_messages = 5

# NPC setup
npc_images = ["http://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Auto_Racing_Black_Box.svg/800px-Auto_Racing_Black_Box.svg.png"]


"""
Functions:
    All of the following functions are "helper functions".
    All of them except clean_dbs are called by at least one 
    Flask route. In the case of clean_dbs, it is called every 
    4 hours. 
    
    They are organized as follows:
        1. get_google_provider_cfg
        2. readify_form_errors
        3. process_character_form
        4. process_room_form
        5. determine_if_user_spamming
        6. character_icon_add_database
        7. character_icon_del_database
        8. clean_dbs
"""

def get_google_provider_cfg():
    """
    The get_google_provider_cfg function. This
    function returns a jsonified get request to
    the GOOGLE_DISCOVERY_URL. This is used when 
    logging a user in.
    """
    return get(GOOGLE_DISCOVERY_URL).json()


def readify_form_errors(form):
    """
    The readify_form_errors function. This
    function takes one of the form validatation
    classes from classes.py and converts the dictionary
    of errors into a list of easy-readable strings.
    This function is only called if a form fails to validate.

    :param form:
        Either a CharacterValidation, RoomValidation
        or UserValidation object depending on the situation.
    """
    error_list = []

    for error in form.errors.keys():
        error_message = error + ": " + form.errors[error][0] +"\n"
        error_list += [error_message]

    return error_list


def process_character_form(form, user_id, usage, route="/characters/create"):
    """
    TODO: Simplify this function. Definitely can
    and should be simplified (logically)

    The process_character_form function. This
    function takes a validation form, the user's id, 
    usage and endpoint route, processes the form,
    and takes action depending on the status of the form.

    There are a two main branches in this function:
    the form validates or it fails to validate.
        1.  The form validates
            Should the form validate, a Tuple of the
            values is created. From here, the usage determines
            the next actions.
            a.  create
                A check is done to see if the user already has a
                character with that name. If so, they are sent back
                to the addition page with a message. Otherwise, the character
                is added to the database and they are sent to view their
                characters.
            b.  edit
                A check is done to see if the new name is not already used (ignoring the
                character being edited). If it is, they are sent back to the
                edit page with a message. Otherwise, the database is updated
                to the new values. If the name was changed, all references
                to that character are updated.
            c.  play
                This route is only used when a user does not have a 
                character and is attempting to join a game. As such,
                their character is added to the database and they are
                sent to their game
        2.  The form fails to validate
            Should the form fail to validate, a list of errors is compiled.
            From here, they are redicted to their specific route and template
            depending on their usage (create, edit and play).
    
    :param form:
        A CharacterValidation object with the information scraped from
        the pages' form.
    :param user_id:
        The id of the user attempting to create/edit a character.
    :param usage:
        Where the user is coming from. Three possible values:
        "create", "edit", "play".
    :param route:
        The endpoint route of where the user is attempting to
        go. Only used in when the usage is "play".
    """
    if form.validate():
        values = (user_id, form.name.data, form.classname.data, form.subclass.data, form.race.data, form.subrace.data, form.speed.data, form.level.data, form.strength.data, form.dexterity.data, form.constitution.data, form.intelligence.data, form.wisdom.data, form.charisma.data, form.hitpoints.data, form.character_token.data or current_user.profile_picture)
    
        if usage == "create":
            if read_db("characters", "*", f"WHERE user_id = '{user_id}' AND character_name = '{values[1]}'") != []:
                app.logger.warning(f"User {current_user.username} already has a character with name {form.name.data}. Reloading the Add Character page to allow them to change the name")
                return render_template("add_character.html", message_text="You already have a character with this name!", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, char_token=form.character_token.data, profile_picture=current_user.profile_picture, username=current_user.username)

            app.logger.debug(f"User {current_user.username} successfully added a character with name {form.name.data}. Redirecting them to the View Characters page.")
            add_to_db("characters", values)

            return redirect(url_for("view_characters"))

        elif usage == "edit":
            if request.form['old_name'] != request.form['name'] and read_db("characters", "*", f"WHERE user_id = '{user_id}' AND character_name = '{request.form['name']}'") != []:
                app.logger.warning(f"User {current_user.username} attempted to change the name of character {request.form['old_name']} to {request.form['name']}. They already have another character with that name. Reloading the Edit Character page to allow them to change the name.")
                return render_template("edit_character.html", message_text="You already have a character with this name!", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.wisdom.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, old_name=request.form['old_name'], char_token=form.character_token.data, profile_picture=current_user.profile_picture, username=current_user.username)

            app.logger.debug(f"Updating the characters owned by user {current_user.username}.")
            delete_from_db("characters", f"WHERE user_id = '{user_id}' AND character_name = '{request.form['old_name']}'")
            add_to_db("characters", values)

            if request.form['old_name'] != form.name.data:
                app.logger.warning(f"User {current_user.username} updating the character name. Updating all of the references to that character in the database.")
                update_db("active_room", f"character_name = '{form.name.data}'", f"WHERE character_name = '{request.form['old_name']}' AND user_id = '{user_id}'")
                update_db("chat", f"username = '{form.name.data}'", f"WHERE username = '{request.form['old_name']}' AND user_id = '{user_id}'")
            
            app.logger.debug(f"User {current_user.username} successfully updated a character with name {form.name.data}. Redirecting them to the View Characters page.")
            return redirect(url_for("view_characters"))
        
        elif usage == "play":
            add_to_db("characters", values)
            app.logger.debug(f"User {current_user.username} successfully created their first character with name {form.name.data}. Redirecting them to the Choose Characters Page")
            return redirect(route)

    error_list = readify_form_errors(form)

    if usage == "create":
        app.logger.warning(f"Character that user {current_user.username} attempted to add had errors. Reloading the Add Character page to allow them to fix the errors.")
        return render_template("add_character.html", errors=error_list, action="/characters/create", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.charisma.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data,  char_token=form.character_token.data, profile_picture=current_user.profile_picture, username=current_user.username)
    
    if usage == "edit": 
        app.logger.warning(f"Character that user {current_user.username} attempted to edit had errors. Reloading the Edit Character page to allow them to fix the errors.")
        return render_template("edit_character.html", errors=error_list, name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.charisma.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data, old_name=request.form['old_name'],  char_token=form.character_token.data, profile_picture=current_user.profile_picture, username=current_user.username)

    if usage == "play":
        app.logger.warning(f"Character user {current_user.username} attempted to add had errors. Reloading Add Character page to allow them to fix the errors.")
        # TODO: Fix the route here
        return render_template("add_character.html", errors=error_list, action="/play/choose", name=form.name.data, hp=form.hitpoints.data, speed=form.speed.data, lvl=form.level.data, str=form.strength.data, dex=form.dexterity.data, con=form.constitution.data, int=form.intelligence.data, wis=form.wisdom.data, cha=form.charisma.data, old_race=form.race.data, old_subrace=form.subrace.data, old_class=form.classname.data, old_subclass=form.subclass.data,  char_token=form.character_token.data, profile_picture=current_user.profile_picture, username=current_user.username)


def process_room_form(form, user_id, usage, room_id):
    """
    TODO: Simplify this function. Definitely can
    and should be simplified (logically)

    The process_room_form. This
    function takes a validation form, the user's id, 
    usage and room id, processes the form,
    and takes action depending on the status of the form.

    There are a two main branches in this function:
    the form validates or it fails to validate.
        1.  The form validates
            Should the form validate, a Tuple of the values
            scraped from the form is made. If the form is being edited,
            its values are updated. Otherwise, the form is added to the
            database.
        2.  The form fails to validate
            Should the form fail to validate, a list of errors is compiled
            and the user is sent back to the form with the errors.
    """
    if form.validate():
        values = (user_id, form.room_name.data, "null", '{}', form.map_url.data, form.dm_notes.data)

        if usage == "create":
            app.logger.debug(f"User {current_user.username} has created the room named {form.room_name.data}")

            add_to_db("room_object", values)
            return redirect(url_for("view_rooms"))

        if usage == "edit":
            app.logger.debug(f"User {current_user.username} has saved changes to the room named {form.room_name.data}")
            
            delete_from_db("room_object", f"WHERE row_id ='{room_id}'")
            add_to_db("room_object", values)
            return redirect(url_for("view_rooms"))

    error_list = readify_form_errors(form)
    if usage == "create":
        app.logger.debug(f"The room {current_user.username} was attempting to create had some errors. Sending back to creation page to fix errors.")
        return render_template("room_create.html", errors=error_list, room_name=form.room_name.data, map_url=form.map_url.data, dm_notes=form.dm_notes.data ,profile_picture=current_user.profile_picture, username=current_user.username )

    if usage == "edit":
        app.logger.debug(f"The room {current_user.username} was attempting to edit had some errors. Sending back to edit page to fix errors.")
        return render_template("room_edit.html", errors=error_list, room_name=form.room_name.data, map_url=form.map_url.data, dm_notes=form.dm_notes.data ,profile_picture=current_user.profile_picture, username=current_user.username )
        

def determine_if_user_spamming(chats, time_received):
    """
    The determine_if_user_spamming function.
    This function looks at a user's chat history
    in a room to determing if they have been spamming
    the chat. If so, they are muted for `spam_penalty`
    seconds.

    This function uses global variables `spam_penalty`,
    `spam_timeout` and `spam_max_messages`

    :param chats:
        The chat history of the user for the room.
    """
    max_messages = spam_max_messages
    timeframe = spam_timeout
    current_time = datetime.datetime.fromisoformat(time_received)
    total_messages_user_sent= 0
    chats.reverse()
    
    for message in chats:
        message_time = datetime.datetime.fromisoformat(message[1])
        if ((current_time - message_time).total_seconds()) < timeframe:
            total_messages_user_sent += 1
        else:
            # TODO: Why is this here?
            break
    if total_messages_user_sent > max_messages:
        return True
    return False


def character_icon_add_database(character_name, username, character_image, user_id, room_id):
    """
    The character_icon_add_database function.
    This function takes a character's name, the
    username of the owner of the character, the
    character's token, the user's id and the room's
    id. Using this information, a character's token
    is added to the database.

    :param character_name:
        The name of the character whose token
        is being stored.
    :param username:
        The username of the user who "owns" the
        character.
    :param character_image:
        The url of the image being using the
        character's token.
    :param user_id:
        The user_id of the owner of the character
    :param room_id:
        The id of the room that the character's token
        is being added to.
    """
    initial_height = "10%"
    initial_width = "10%"
    initial_top = "10%"
    initial_left = "10%"

    map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    
    wrong_room = []
    for i in map_status:
        if map_status[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del map_status[i]

    user_id_character_name = str(user_id) + '_' + str(character_name)
    json_character_to_add = { user_id_character_name: {"username": username, "character_name": character_name, "room_id": room_id, "character_image": character_image, "height": initial_height, "width": initial_width, "top": initial_top, "left": initial_left, "is_turn": 0}}
    map_status[user_id_character_name] = json_character_to_add[user_id_character_name]
    map_status_json = json.dumps(map_status)
    update_db("room_object", f"map_status = '{map_status_json}'", f"WHERE active_room_id = '{room_id}'")

    updated_character_icon_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    emit('redraw_character_tokens_on_map', updated_character_icon_status, room=room_id)


def character_icon_del_database(character_name, username, user_id, room_id ):
    """
    The character_icon_del_database function.
    This function takes a character's name, the
    username of the owner of the character, 
    the user's id and the room's
    id. Using this information, a character's token
    is removed from the database.

    :param character_name:
        The name of the character whose token
        is being deleted.
    :param username:
        The username of the user who "owns" the
        character..
    :param user_id:
        The user_id of the owner of the character
    :param room_id:
        The id of the room that the character's token
        is being deleted from.
    """
    map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    
    wrong_room = []
    for i in map_status:
        if map_status[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del map_status[i]


    character_name = " ".join(character_name.split("_"))
    
    user_id_character_name = str(user_id) + '_' + str(character_name)

    del map_status[user_id_character_name]
    map_status_json = json.dumps(map_status)
    
    update_db("room_object", f"map_status = '{map_status_json}'", f"WHERE active_room_id = '{room_id}'" )

    updated_character_icon_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    emit("redraw_character_tokens_on_map", updated_character_icon_status, room=room_id)


def clean_dbs():
    """
    The clean_dbs function. This function
    goes through the active_room table and
    removes any rooms that have not been updated
    within 24 hours. Subsequently, it also removes
    chats and logs from the table from the
    rooms that are deleted
    """
    current_time = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    benchmarktime = current_time - datetime.timedelta(hours=24)
    open_rooms_past_due = read_db("log", "DISTINCT room_id", f"WHERE timestamp > {benchmarktime} ORDER BY timestamp")
    for room_id in open_rooms_past_due:
        delete_from_db("active_room", f"WHERE room_id = '{room_id[0]}'")
        delete_from_db("chat", f"WHERE room_id = '{room_id[0]}'")
        delete_from_db("log", f"WHERE room_id = '{room_id[0]}'")
        update_db("room_object", "active_room_id = 'null'", f"WHERE active_room_id = '{room_id[0]}'")

scheduler.add_job(func=clean_dbs, trigger="cron", hour=3, minute=59)

"""
login_manager "Helper" functions:
    The login_manager "helper" functions are
    functions written to handle users connecting
    to the appication. 
    
    They are organized as follows:
        1.  load_user
        2.  sent_to_login

"""
@login_manager.user_loader
def load_user(user_id):
    """
    The load_user function. This function is called
    whenever a user loads a page. This function reads
    the user table looking for a matching user_id. If it
    finds a match, a User object is returned. Otherwise
    None is returned and an AnonymousUser object is created.

    :param user_id:
        The user_id gotten from Google OAuth
    """
    db_response = read_db("users", "*", f"WHERE user_id = '{user_id}'")
    if not db_response:
        return None
    return User(id_=db_response[0][0], email=db_response[0][1], profile_picture=db_response[0][2], username=db_response[0][3])


@login_manager.unauthorized_handler
def sent_to_login():
    """
    The sent_to_login function. This function
    is called whenever a user who is not logged
    in attempts to load a route that has the decorator
    `login_required`.
    """
    return redirect(url_for("login_index"))


"""
Routing Directives:
    All of the following functions are
    the specific routing directives that
    are on the app. All of these functions
    have the @app.route decorate which specifies
    the route and allowed methods.

    Additionally, some may have the @login_required
    decorator, which means that a user must be logged
    in to access that route. 
    
    They are organized as follows (labeled as the 
    routes rather than the functions):
        1.  /characters
        2.  /characters/create
        3.  /characters/edit/<name>
        4.  /home
        5.  /user/settings
        6.  /rooms
        7.  /rooms/create
        8.  /rooms/<room_id>
        9.  /generate_room
        10. /play/<room_id>
        11. /spectate/<room_id>
        12. /
        13. /login
        14. /login/callback
        15. /logout
        16. /delete
"""

@app.route("/characters", methods=["GET", "POST"])
@login_required
def view_characters():
    """
    The /characters route. This route allows
    users to see all of their characters. It has 
    two main paths depending on the method used.
    
    If the method is GET, the route determines the 
    user's id, and using that id, grabs all of the
    characters owned by the id. It then uses that
    character list and loads the view_characters.html 
    template.

    Otherwise, if the method is POST, the user is
    deleting a character. The route does everything
    the GET section does, as well as deleting the
    character from both the `characters` table
    and the `active_room` table.
    """
    user_id = current_user.id

    if request.method == "POST":
        app.logger.debug(f"Attempting to delete character owned by {current_user.username} named {request.form['character_name']}.")
        delete_from_db("characters", f"WHERE user_id = '{user_id}' AND character_name = '{request.form['character_name']}'")
        delete_from_db("active_room", f"WHERE user_id = '{user_id}' AND character_name = '{request.form['character_name']}'")
                        
    characters = read_db("characters", "*", f"WHERE user_id = '{user_id}'")
    app.logger.debug(f"User {current_user.username} has gone to view their characters. They have {len(characters)} characters.")
    return render_template("view_characters.html", items=characters, profile_picture=current_user.profile_picture, username=current_user.username)


@app.route("/characters/create", methods=["POST","GET"])
@login_required
def character_creation():
    """
    The /characters route. The route allows users
    to create characters. First, it determines
    the user's id and grabs the form route from the URL
    (`route=` argument). Additionally, it grabs the form
    even if the method is GET. From here, the route diverges
    depending on the method.

    If the method is GET, the form action is set to
    this route, `/characters/create`, and the
    add_character.html template is loaded.

    Otherwise, the method is POST. The function calls
    `process_character_form` and returns whatever is
    returned from that function.

    :param route:
        The desired endpoint of the form character
        creation form. Grabbed from the URL instead
        embedded within the route definition.
    """
    route = request.args.get('route')

    if request.method == "POST":
        form = CharacterValidation()
        user_id = current_user.id

        app.logger.debug(f"User {current_user.username} is attempting to register a character with name {form.name.data}.")
        if route:
            return process_character_form(form, user_id, "play", route)
            
        return process_character_form(form, user_id, "create")

    app.logger.debug(f"User {current_user.username} has gone to add a character.")
    action = "/characters/create"
    if route:
        action += f"?route={route}"
    return render_template("add_character.html", profile_picture=current_user.profile_picture, username=current_user.username, action=action)


@app.route("/characters/edit/<name>", methods=["GET", "POST"])
@login_required
def edit_character(name):
    """
    The /characters/edit/<name> route. This
    route allows users to edit characters
    that they own. First, the route grabs the user's 
    id and form regardless of the method used. From 
    here, the method diverges depending on the method.

    If the method is GET, the route attempts to load
    the character specific by the `name` variable. If
    it cannot load the character, it throws a BadRequest
    error. Otherwise, if the character is loaded, the
    edit_character.html template is loaded.

    On the other hand, if the method is POST,
    the route calls the `process_character_form`
    function and returns whatever is returned
    from the function call.

    :param name:
        The name of the character the user
        is attempting to edit.
    """
    if request.method == "POST":
        user_id = current_user.id
        form = CharacterValidation()

        app.logger.warning(f"User {current_user.username} is attempting to update a character with name {request.form['old_name']}.")
        return process_character_form(form, user_id, "edit")

    character = read_db("characters", "*", f"WHERE user_id = '{current_user.id}' AND character_name = '{name}'")

    if character:
        character = character[0]
        app.logger.debug(f"User {current_user.username} has gone to edit a character with name {character[1]}.")
        return render_template("edit_character.html", name=character[1], hp=character[14], old_race=character[4], old_subrace=character[5], old_class=character[2], old_subclass=character[3], speed=character[6], lvl=character[7], str=character[8], dex=character[9], con=character[10], int=character[11], wis=character[12], cha=character[13], old_name=character[1], char_token=character[15], profile_picture=current_user.profile_picture, username=current_user.username)

    app.logger.warning(f"User attempted to edit a character with name {name}. They do not have a character with that name. Throwing a Bad Request error.")
    raise BadRequest(description=f"You don't have a character named {name}!")


#TODO: Find way to cache guest users when they go onto the website
#TODO: Create generalized function that can grab authorized users who skip the site name
@app.route("/home", methods=["GET", "POST"])
def home():
    """
    The /home route. This route displays
    the home page to the user. First, it
    determines if the user is logged in 
    then diverges depending on the method.

    If the method is GET and the user is
    not logged in, the login.html template
    is loaded. Otherwise, if the user is
    logged in and they have a username,
    the home.html page is loaded. Finally, if
    the user is logged in but does not have
    a username, the set_username.html page
    is loaded

    If the method is POST, the user is
    setting their username. If their
    form validates, they are redirected
    to the /home route with a GET request.
    Otherwise, the set_username.html template
    is reloaded (with their information still
    there) with an error message.
    """
    authenticated = False
    if current_user.is_authenticated:
        app.logger.debug(f"User logged in")
        authenticated = True
    else:
        app.logger.debug(f"User not logged in")

    if request.method == "POST":
        if "username" in request.form:
            username = request.form["username"]

            form = UsernameValidation()

            if not form.validate():
                error_list = readify_form_errors(form)
                app.logger.warning(f"There were errors in the chosen site name. Reloading the page")
                return render_template("set_username.html", errors=error_list, error_username=username, profile_picture=current_user.profile_picture, username=current_user.username)

            app.logger.debug(f"User is attempting to set their site name as {username}")
            if read_db("users", "*", f"WHERE username = '{username}'"):
                app.logger.warning(f"Site name {username} already has been used. Reloading the Set User Name with warning message.")
                return render_template("set_username.html", message="Another user has that username!" ,error_username=username, profile_picture=current_user.profile_picture, username=current_user.username)

            app.logger.debug(f"{username} is available as a site name. Adding it to the user.")
            update_db("users", f"username = '{username}'", f"WHERE user_id = '{current_user.id}'")
            return redirect(url_for('home'))

        if "spectate_room_id" in request.form:
            room_id = request.form['spectate_room_id']

            if read_db("room_object", "*", f"WHERE active_room_id = '{room_id}'"):
                app.logger.debug(f"{current_user.username} is entering the room {room_id}")
                return redirect(url_for('spectateRoom', room_id=room_id))
            
            app.logger.warning(f"User {current_user.username} attempted to enter an nonexistant room. Reloading to form with a message")
            if authenticated:
                return render_template("home.html", spectate_message= "There is not an open room with that key!", spectate_room_id=room_id, profile_picture=current_user.profile_picture, username=current_user.username)
            else:
                return render_template("login.html", spectate_message= "There is not an open room with that key!", spectate_room_id=room_id, profile_picture=current_user.profile_picture, username=current_user.username)
                

        if "play_room_id" in request.form:
            room_id = request.form['play_room_id']

            if read_db("room_object", "*", f"WHERE active_room_id = '{room_id}'"):
                app.logger.debug(f"User {current_user.username} is entering room {room_id}")
                return redirect(url_for('enterRoom', room_id=room_id))
            
            app.logger.warning(f"User {current_user.username} attempted to enter an nonexistant room. Reloading to form with a message")
            return render_template("home.html", play_message="There is not an open room with that key!", play_room_id=room_id, profile_picture=current_user.profile_picture, username=current_user.username)

    if not authenticated:
        return render_template("login.html", profile_picture=current_user.profile_picture, username=current_user.username)

    if not current_user.username:
        app.logger.warning("User does not have site name. Loading the Set User Name page.")
        return render_template("set_username.html", profile_picture=current_user.profile_picture, username=current_user.username)

    app.logger.debug(f"Rooms in Database:")
    for i in read_db("room_object"):
        app.logger.debug(f"{i}")
    app.logger.debug(f"Active Rooms in Database:")
    for i in read_db("active_room"):
        app.logger.debug(f"{i}")

    return render_template("home.html", profile_picture=current_user.profile_picture, username=current_user.username)


@app.route("/user/settings", methods=["GET", "POST"])
@login_required
def user_settings():
    """
    The user_settings route. This route
    allows users to change their account
    settings. First, itdetermines the user's 
    id, grabs all of their characters and 
    determines the user's email. From here, the 
    route diverges depending on the method.

    If the method is GET, the user_settings.html
    template is loaded. That's it.

    Otherwise, when the method is POST, the
    route determines what has been changed
    in the form and validates the form.
    If the form validates, the user_settings.html
    template is loaded with the updated information.
    If the form fails to validate, the user_settings.html
    template is loaded with an error message.
    """
    user_id = current_user.id
    characters = read_db("characters", "character_name, char_token", f"WHERE user_id = '{user_id}'")
    user_email = current_user.email

    if request.method == "POST":
        if 'username' in request.form and request.form['username'] != current_user.username:
            new_username = request.form['username']

            form = UsernameValidation()

            if not form.validate():
                error_list = readify_form_errors(form)
                app.logger.warning(f"There are issues in the renaming form. Allowing the user to change it")
                return render_template("user_settings.html", characters=characters, username_errors=error_list, new_username=new_username, profile_picture=current_user.profile_picture, username=current_user.username, user_email=user_email)

            if read_db("users", "*", f"WHERE username = '{new_username}'"):
                app.logger.warning(f"Site name {new_username} already has been used. Reloading the user settings page with warning message.")
                return render_template("user_settings.html", characters=characters, username_message="That username is already in use!", new_username=new_username, profile_picture=current_user.profile_picture, username=current_user.username, user_email=user_email)

            app.logger.debug(f"{new_username} is available as a site name. Updating {current_user.username} site name.")
            update_db("users", f"username = '{new_username}'", f"WHERE user_id = '{user_id}'")
            return redirect(url_for('user_settings'))

    app.logger.debug(f"User {current_user.username} is accessing their user settings")
    return render_template("user_settings.html", characters=characters, new_username=current_user.username, profile_picture=current_user.profile_picture, username=current_user.username, user_email=user_email)


@app.route("/rooms", methods=["GET", "POST"])
@login_required
def view_rooms():
    """
    The /rooms route. This route allows users
    to see all rooms that they have created.
    It is entirely dependent on the method used.

    If the method is GET, the route loads
    all of the rooms in the room_object that
    are owned by the user and loads the view_rooms.html
    template.

    Otherwise, if the method is POST, the user
    is attempting to delete a room. If the `room_id`
    of the room is being used by an active room, the view_rooms.html
    template is loaded with an error message. Else, the
    room is deleted from the room_object table and the
    user is redirected to the /rooms route with the GET method.
    """
    if request.method == "POST":
        app.logger.debug(f"Attempting to delete room owned by {current_user.username} named {request.form['room_name']}.")
        
        if read_db("active_room", "room_id", f"WHERE room_id = {request.form['room_id']}"):
            app.logger.warning(f"User {current_user.username} is attempting to delete an active room {request.form['room_name']}")
            # Do we want this responsibility to be on the user or is there merit to just scrubbing the DBs from this page
            return render_template("view_rooms.html" , message="Room is active! Close it first!", profile_picture=current_user.profile_picture, username=current_user.username, room_list=created_rooms)
        
        delete_from_db("room_object", f"WHERE row_id = {request.form['room_id']}")
        app.logger.debug(f"Deleted user {current_user.username}'s room {request.form['room_name']}")
        return redirect(url_for('view_rooms'))

    app.logger.debug(f"User {current_user.username} has gone to the rooms page.")

    created_rooms = read_db("room_object", "row_id, room_name, map_url, dm_notes, active_room_id", f"WHERE user_id = '{current_user.id}'")

    active_rooms = []
    for room in created_rooms:
        if room[4] != "null":
            active_rooms.append(room)

    return render_template("view_rooms.html", profile_picture=current_user.profile_picture, username=current_user.username, room_list=created_rooms, active_rooms=active_rooms)


@app.route("/rooms/create", methods=["GET", "POST"])
@login_required
def room_creation():
    """
    The /rooms/create route. This route
    allows uses to create new room. First, 
    it grabs the form and user's id regardless
    of the method used. From here, the route
    diverges depending on the method used.

    If the method is GET, the add_room.html
    template is loaded.

    Otherwise, when the method is POST, the
    `process_room_form` function is called and
    whatever is returned by the `process_room_form`
    function is returned.
    """
    app.logger.debug(f"User {current_user.username} is creating a new room!")
    form = RoomValidation()
    user_id = current_user.id

    if request.method == "POST":
        app.logger.debug(f"User {current_user.username} is attempting to create a new room")
        return process_room_form(form, user_id, "create", "")

    return render_template("room_create.html", profile_picture=current_user.profile_picture, username=current_user.username, map_url="https://i.pinimg.com/564x/b7/7f/6d/b77f6df018cc374afca057e133fe9814.jpg")


@app.route("/rooms/<room_id>", methods=["GET", "POST"])
@login_required
def room_edit(room_id):
    """
    The /rooms/<room_id> route. This
    route allows users to edit previously
    created rooms. First, it determines the 
    user's id and pulls the form regardless 
    of the method used. From here, the route 
    diverges depending on the method used.

    If the method is GET, the route attempts
    to load the room the specified `room_id`.
    If the room does not exist, a BadRequest
    error is thrown. Otherwise, the edit_room.html
    template is loaded.

    Else, when the method is POST, the route
    calls the `process_room_form` function and
    returns whatever is returned from that function.

    :param room_id:
        The id of the room the user is attempting
        to access
    """
    user_id = current_user.id
    form = RoomValidation()

    if request.method == "POST":
        app.logger.warning(f"User {current_user.username} is attempting to edit their room")
        return process_room_form(form, user_id, "edit", room_id)

    room = read_db("room_object", "*", f"WHERE row_id = {room_id} and user_id= '{current_user.id}'")
    if room:
        room = room[0]
        app.logger.debug(f"User {current_user.username} is prepping their room for their encounter!")
        return render_template("room_edit.html", profile_picture=current_user.profile_picture, username=current_user.username, map_url= room[5], room_name=room[2], dm_notes = room[6], room_id=room_id )

    app.logger.warning(f"User attempted to prep a room with name {room_id}. They do not have a room with that id. Throwing a Bad Request error.")
    raise BadRequest(description=f"You don't have a room with id: {room_id}!")


@app.route("/generate_room", methods=["POST"])
@login_required
def generate_room_id():
    """
    The /generate_room route. This route generates
    a new active room that the use can then use. 
    This route takes the name of a room and the user's 
    id to generate an active room. Once the room is generated, 
    the user is redirected to the /play/<room_id> route.
    """
    user_id = current_user.id
    room_name = request.form["room_id"]
    random_key = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))

    while read_db("room_object", "*", f"WHERE active_room_id = '{random_key}'"):
        random_key = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))

    update_db("room_object", f"active_room_id = '{random_key}'", f"WHERE user_id = '{user_id}' AND row_id = '{room_name}'")

    return redirect(url_for('enterRoom', room_id=random_key))


@app.route("/play/<room_id>", methods=["GET", "POST"])
@login_required
def enterRoom(room_id):
    """
    The /play/<room_id> route. This route
    allows a user to enter an active room.

    The method determines the user's id, the
    battle map and the owner of the room. If the
    specified room does not exist, a BadRequest error
    is thrown.

    Assuming the room exists, all of the user's characters
    are loaded. If the user does not have any characters, they
    are redirected to the /characters/create route.

    If the user is the owner of the map, the play_dm.html template
    is loaded. Otherwise, the play.html template is loaded.

    :param room_id:
        The public id of the room the user to 
        which the user is attempting to connect.
    """
    user_id = current_user.id
    try:
        image_url, map_owner = read_db("room_object", "map_url, user_id", f"WHERE active_room_id = '{room_id}'")[0]
        characters = read_db("characters", "character_name", f"WHERE user_id='{user_id}'")

        if not characters:
            return redirect(url_for("character_creation", route=f"/play/{room_id}"))

        app.logger.debug(f"User {current_user.username} has entered the room {room_id}")
        if user_id == map_owner:
            return render_template("play_dm.html", async_mode=socketio.async_mode, characters=characters, in_room=room_id, image_url=image_url, profile_picture=current_user.profile_picture, username=current_user.username)
        else:
            return render_template("play.html", async_mode=socketio.async_mode, characters=characters, in_room=room_id, image_url=image_url, profile_picture=current_user.profile_picture, username=current_user.username)

    except:
        app.logger.debug(f"No such room exists")
        raise BadRequest(description=f"A room with room id {room_id} does not exist!")


@app.route("/spectate/<room_id>", methods=["GET", "POST"])
def spectateRoom(room_id):
    """
    The /spectate/<room_id> route. This route
    allows a user to spectate the specified room.

    Should the room not exist, a BadRequest error
    is thrown. If the room does exist, the battle
    map is loaded. If the user is logged in, the
    watch.html template is loaded. Otherwise, the
    unlogged_watch.html template is laoded.

    :param room_id:
        The id of the room the user is 
        attempting to spectate.
    """
    try:
        image_url = read_db("room_object", "map_url", f"WHERE active_room_id = '{room_id}'")[0][0]

        app.logger.debug(f"User {current_user.username} is spectating the room {room_id}")

        if current_user.is_authenticated:
            return render_template("watch.html", async_mode=socketio.async_mode, in_room=room_id, image_url=image_url, profile_picture=current_user.profile_picture, username=current_user.username)
        return render_template("unlogged_watch.html", async_mode=socketio.async_mode, in_room=room_id, image_url=image_url, profile_picture=current_user.profile_picture, username=current_user.username)

    except:
        app.logger.debug(f"No such room exists")
        raise BadRequest(description=f"A room with room id {room_id} does not exist!")


@app.route("/")
def login_index():
    """
    The / route. This is the most basic route,
    and just redirectes the user to the /home
    route.
    """
    return redirect(url_for('home'))


@app.route("/login")
def login():
    """
    The /login route. This route ensures
    that the application is authorized
    to use Google OAuth. When authorized,
    the user is redirected to the /login/callback route.
    """
    # Get the authorization endpoint for Google login
    authorization_endpoint = get_google_provider_cfg()["authorization_endpoint"]
    # Use client.prepare_request_uri to build the request to send to Google, and specify the information we want from the user
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    """
    The /login/callback route. This route
    sends login information to Google. When 
    the user is logged into Google, Google
    sends the user's Google ID, email and
    URL to their profile picture.

    The user is then added to the user table
    if they are not already present, and they
    are then logged in. From here, they are
    redirected to the / route.
    """
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
    else:
        return "User email not available or not verified by Google.", 400
    # Create a user in the datbase if they don't already exist
    user = User(id_=unique_id, email=users_email, profile_picture=picture, username=None)
    if not read_db("users", "*", f"WHERE user_id = '{unique_id}'"):
        add_to_db("users", (unique_id, users_email, picture, None))
    # Log the user in and send them to the homepage
    login_user(user)
    return redirect(url_for("login_index"))


# Logout
@app.route("/logout")
@login_required
def logout():
    """
    The /logout route. This route determines
    the user accessing it and logs them out.
    """
    app.logger.debug(f"User {current_user.username} just logged out")
    logout_user()
    return redirect(url_for("login_index"))


# Delete Account
@app.route("/delete")
@login_required
def delete_account():
    """
    The /delete route. This route determines
    the user accessing this route and then deletes
    anything related to their account, including
    the account itself from the database. They are then
    redirected to the / route.

    This cannot be undone.
    """
    user_id = current_user.id
    app.logger.debug(f"User {current_user.username} is deleting their account. Deleting all associated information")
    delete_from_db("log", f"WHERE user_id = '{user_id}'")
    delete_from_db("chat", f"WHERE user_id = '{user_id}'")
    delete_from_db("active_room", f"WHERE user_id = '{user_id}'")
    delete_from_db("room_object", f"WHERE user_id = '{user_id}'")
    delete_from_db("users", f"WHERE user_id = '{user_id}'")
    delete_from_db("characters", f"WHERE user_id = '{user_id}'")
    return redirect(url_for("login_index"))


"""
API Routing Directives:
    The following functions are the routing
    directives for the API. All of the routes
    in this section all start with `/api/`. The
    API is meant for internal use, and as such,
    only functions as needed by the application.
    
    The routes are organized as follows:
        1.  /api/races
        2.  /api/classes
"""
@app.route("/api/races")
@login_required
def get_races():
    """
    The /api/races route. This route
    returns a jsonified representation
    of all the races and subraces used
    by the edit_character.html and
    add_charater.html templates
    """
    races, subraces = get_api_info("race", "race")
    return jsonify(races=list(races), subraces=subraces)

@app.route("/api/classes")
@login_required
def get_classes():
    """
    The /api/classes route. This route
    returns a jsonified representation
    of all the classes and subclasses 
    used by the edit_character.html and
    add_character.html templates.
    """
    classes, subclasses = get_api_info("class", "class")
    return jsonify(classes=list(classes), subclasses=subclasses)


"""
SocketIO Handlers:
    The following functions are all SocketIO
    event handlers. All of them are decorated
    with `@socketio.on('event_name', namespace='/combat')`.
    
    All of these functions have one parameter, message,
    which is a dictionary received from the frontend.
    
    The functions are ordered as follows:
        1.  set_initiative
        2.  send_chat
        3.  start_combat
        4.  end_combat
        5.  end_room
        6.  end_turn
        7.  get_sid
        8.  on_join
        9.  join_actions
        10. character_icon_update_database
        11. add_character
        12. remove_character
        13. add_npc
"""


@socketio.on('set_initiative', namespace='/combat')
def set_initiative(message):
    """
    The set_initiative event handler. This
    function set or update a character's initiative 
    in the given room. It then sends out the initiative
    update to all clients in the room.

    :message:
        A dictionary with the following keys:
            character_name: Name of the character
                            whose initiative is being
                            updated.
            initiative:     New initiative value
            username:       Username of the owner
                            of the character.
            room_id:        The room id of the
                            active battle
    """
    time_received = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    character_name = message['character_name'] or None
    initiative = message['init_val']
    username = message['username']
    room_id = message['room_id']
    user_id = current_user.id

    if not character_name and not initiative:
        return

    description = f"{character_name}'s initiative updated in room {room_id}"
    app.logger.debug(f"Battle update: {description}.")

    if not initiative:
        initiative = read_db("active_room", "init_val", f"WHERE room_id = '{room_id}' AND user_id = '{user_id}' AND character_name = '{character_name}'")[0][0]

    update_db("active_room", f"init_val = '{initiative}'", f"WHERE room_id = '{room_id}' AND user_id = '{user_id}' AND character_name = '{character_name}'")
    add_to_db("log", (room_id, user_id, "Init", description, time_received))

    emit('initiative_update', {'character_name': character_name, 'init_val': initiative, 'username': username}, room=room_id)
    emit('log_update', {'desc': description}, room=room_id)


@socketio.on('send_chat', namespace='/combat')
def send_chat(message):
    """
    The send_chat event handler. This
    function receives a request from a
    client to send a chat in the given room.
    If they have not been spamming the chat, 
    they chat is sent to all connected clients
    in the room. Otherwise, the original client
    is notified that they were spamming the chat.

    :message keys:
        chat:       The message the user is 
                    attempting to send to the room
        username:   The username of the user
                    sending the chat
        room_id:    The id of the room the
                    client is in
    """
    time_received = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.id
    username = message['character_name']
    room_id = message['room_id']
    chat = message['chat']
    username = current_user.username

    chats = read_db("chat", "user_id, timestamp", f"WHERE room_id = '{room_id}' and user_id = '{user_id}'")

    if determine_if_user_spamming(chats, time_received):
        add_to_db("log", (room_id, user_id, "Spam", f"{username} was spamming the chat. They have been disabled for {spam_penalty} seconds", time_received))
        emit("lockout_spammer", {'message': f"Sorry, you can only send {spam_max_messages} messages per {spam_timeout} seconds. Try again in {spam_penalty} seconds.", 'spam_penalty': spam_penalty})
        emit('log_update', {'desc': f"{username} was spamming the chat. They have been disabled for {spam_penalty} seconds"}, room=room_id)
        app.logger.debug(f"{username} was spamming the chat. They have been disabled for {spam_penalty} seconds")

    else:
        add_to_db("chat",(room_id, user_id, username, chat, time_received))
        add_to_db("log", (room_id, user_id, "Chat", username, time_received))
        emit('chat_update', {'chat': chat, 'character_name': username}, room=room_id)
        app.logger.debug(f"Battle update: {username} has sent chat `{chat}` in room {room_id}")


# TODO: Button to hide or show character icon on map
@socketio.on('start_combat', namespace='/combat')
def start_combat(message):
    """
    The start_combat event handler. This function
    starts combat in the given room. The character
    with the highest initiative has their is_turn
    variable set to true (literally all that needs
    to happen on the backend). It then sends out
    the `combat_started` to all clients in the room.

    :message keys:
        desc:       A two-word description of the event
        room_id:    The id of the room where combat
                    is starting
    """
    time_received = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.id
    room_id = message['room_id']
    characters = read_db("active_room", "user_id, character_name, init_val", f"WHERE room_id = '{room_id}' ORDER BY init_val, character_name DESC ")
    first_character = characters[-1]
    character_id = first_character[0]
    character_name = first_character[1]
    username = read_db("users", "username", f"WHERE user_id = '{first_character[0]}'")[0][0]
    app.logger.debug(f"Battle update: Combat has started in room {room_id}")

    map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    
    
    wrong_room = []
    for i in map_status:
        if map_status[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del map_status[i]

    user_id_character_name = str(user_id) + '_' + str(character_name)
    json_character_to_update = { user_id_character_name: {"username": username, "character_name": character_name, "room_id": room_id, "character_image": map_status[user_id_character_name]['character_image'], "height": map_status[user_id_character_name]['height'], "width": map_status[user_id_character_name]['width'], "top": map_status[user_id_character_name]['top'], "left": map_status[user_id_character_name]['left'], "is_turn": 1}}
    map_status[user_id_character_name] = json_character_to_update[user_id_character_name]
    characters_json = json.dumps(map_status)
    update_db("room_object", f"map_status = '{characters_json}'", f"WHERE active_room_id = '{room_id}'")

    update_db("active_room", f"is_turn = '{1}'", f"WHERE room_id = '{room_id}' AND user_id = '{first_character[0]}' AND character_name = '{first_character[1]}' AND init_val = '{first_character[2]}'")
    add_to_db("log", (room_id, user_id, "Combat", "Started Combat", time_received))

    emit('log_update', {'desc': "Started Combat"}, room=room_id)
    emit('combat_started', {'desc': 'Started Combat', 'first_turn_name': first_character[1], 'username': username}, room=room_id)


@socketio.on('end_combat', namespace='/combat')
def end_combat(message):
    """
    The end_combat event handler. This function
    ends combat in a given room. The character whose
    turn it is has their is_turn variable set to false
    and the update is sent to all connected clients.

    :message keys:
        desc:       A two-word description of the event
        room_id:    The id of the room where combat
                    is ending
    """
    time_received = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.id
    room_id = message['room_id']
    character = read_db("active_room","user_id, character_name", f"WHERE room_id = '{room_id}' AND is_turn = '1'")[0]
    character_id = character[0]
    character_name = character[1]
    username = read_db("users", "username", f"WHERE user_id = '{character[0]}'")[0][0]
    app.logger.debug(f"Battle update: Combat has ended in room {room_id}")
    user_id = character[0]

    map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    
    wrong_room = []
    for i in map_status:
        if map_status[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del map_status[i]

    user_id_character_name = str(user_id) + '_' + str(character_name)
    json_character_to_update = { user_id_character_name: {"username": username, "character_name": character_name, "room_id": room_id, "character_image": map_status[user_id_character_name]['character_image'], "height": map_status[user_id_character_name]['height'], "width": map_status[user_id_character_name]['width'], "top": map_status[user_id_character_name]['top'], "left": map_status[user_id_character_name]['left'], "is_turn": 0}}
    map_status[user_id_character_name] = json_character_to_update[user_id_character_name]
    characters_json = json.dumps(map_status)
    update_db("room_object", f"map_status = '{characters_json}'", f"WHERE active_room_id = '{room_id}'")

    update_db("active_room", f"is_turn = '{0}'", f"WHERE room_id = '{room_id}'")
    add_to_db("log", (room_id, user_id, "Combat", "Ended Combat", time_received))

    emit('log_update', {'desc': "Ended Combat"}, room=room_id)
    emit('combat_ended', {'desc':'Ended Combat', 'current_turn_name': character[1], 'username': username}, room=room_id)


@socketio.on('end_room', namespace='/combat')
def end_session(message):
    """
    The end_room event handler. This function
    completely removes an active room from the 
    database. The update is then pushed out to the
    connected users.

    :message keys:
        desc:       A two-word description of the event
        room_id:    The id of the room where the room
                    is closing
    """
    room_id = message['room_id']
    delete_from_db("active_room", f"WHERE room_id = '{room_id}'")
    delete_from_db("chat", f"WHERE room_id = '{room_id}'")
    delete_from_db("log", f"WHERE room_id = '{room_id}'")
    update_db("room_object", "map_status = '{}'", f"WHERE active_room_id = '{room_id}'")
    # TODO: Update this so it works with multiple rooms. It will scrub the connected between
    #       all rooms should one room_object have multiple active rooms.
    update_db("room_object", "active_room_id = 'null'", f"WHERE active_room_id = '{room_id}'")

    app.logger.debug(f"The room {room_id} owned by {current_user.username} has closed")
    
    emit("room_ended", {'desc': message['desc']}, room=room_id)
    close_room(room_id)


@socketio.on('end_turn', namespace='/combat')
def end_turn(message):
    """
    The end_turn event handler. This function
    ends a character's turn and moves to the next
    character in the initative order. The update 
    is the pushed out to all connected clients.

    :message keys:
        desc:                       A description of what occurred
        previous_character_name:    The name of the character whose
                                    turn just ended
        next_character_name:        The name of the character whose
                                    turn just begun
        previous_username:          The username of the owner of the
                                    character whose turn just ended
        next_username:              The username of the owner of the
                                    character whose turn just begun
    """
    time_received = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    previous_character_name = message['previous_character_name']
    next_character_name = message['next_character_name']
    previous_username = message['previous_username']
    previous_character_id = read_db("users", "user_id", f"WHERE username = '{previous_username}'")[0][0]
    next_username = message['next_username']
    room_id = message['room_id']
    next_character_id = read_db("users", "user_id", f"WHERE username = '{next_username}'")[0][0]
    app.logger.debug(f"Battle update: {previous_character_name}'s turn has ended. It is now {next_character_name}'s turn in room {room_id}")

    map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    
    wrong_room = []
    for i in map_status:
        if map_status[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del map_status[i]

    previous_user_id_character_name = str(previous_character_id) + '_' + str(previous_character_name)
    next_user_id_character_name = str(next_character_id) + '_' + str(next_character_name)
    previous_json_character_to_update = { previous_user_id_character_name: {"username": previous_username, "character_name": previous_character_name, "room_id": room_id, "character_image": map_status[previous_user_id_character_name]['character_image'], "height": map_status[previous_user_id_character_name]['height'], "width": map_status[previous_user_id_character_name]['width'], "top": map_status[previous_user_id_character_name]['top'], "left": map_status[previous_user_id_character_name]['left'], "is_turn": 0}}
    next_json_character_to_update = { next_user_id_character_name: {"username": next_username, "character_name": next_character_name, "room_id": room_id, "character_image": map_status[next_user_id_character_name]['character_image'], "height": map_status[next_user_id_character_name]['height'], "width": map_status[next_user_id_character_name]['width'], "top": map_status[next_user_id_character_name]['top'], "left": map_status[next_user_id_character_name]['left'], "is_turn": 1}}
    map_status[previous_user_id_character_name] = previous_json_character_to_update[previous_user_id_character_name]
    map_status[next_user_id_character_name] = next_json_character_to_update[next_user_id_character_name]
    characters_json = json.dumps(map_status)
    update_db("room_object", f"map_status = '{characters_json}'", f"WHERE active_room_id = '{room_id}'")

    update_db("active_room", f"is_turn = '{0}'", f"WHERE room_id = '{room_id}'AND user_id = '{previous_character_id}' AND character_name = '{previous_character_name}'")
    update_db("active_room", f"is_turn = '{1}'", f"WHERE room_id = '{room_id}' AND user_id = '{next_character_id}' AND character_name = '{next_character_name}'")
    add_to_db("log", (room_id, previous_character_id, "Combat", f"{previous_character_name}'s Turn Ended", time_received))

    emit('log_update', {'desc': message['desc']}, room=room_id)
    emit("turn_ended", {'desc': message['desc'], 'previous_username': previous_username, 'next_username': next_username}, room=room_id)


@socketio.on("get_sid", namespace="/combat")
def get_sid(message):
    """
    The get_sid event handler. This function
    is only used in the tests. It emits an
    event to the client with it's socketio
    id 
    """
    emit('sid', {'id': request.sid})


@socketio.on('on_join', namespace='/combat')
def on_join(message):
    """
    The on_join event handler. This function
    has a client connect to the SocketIO room
    when they first join a room. Preps the client
    and backend to "catch up" the client to what
    is occurring in the room.

    :message keys:
        room_id:    The id of the room which
                    they just joined.
    """
    app.logger.debug(f"Battle update: User {current_user.username} has entered room {message['room_id']}")
    join_room(message['room_id'])
    
    emit('joined', {'desc': 'Joined room'})


@socketio.on('join_actions', namespace='/combat')
def connect(message):
    """
    The join_actions event handler. This function
    "catches a user who just joined the room up" with
    what has occurred. All of their characters that already
    are in the room are removed from their "Add character" select
    and added to their "update initiative" select. Likewise, they
    recieve all characters in the room and their initiatives. Then,
    they receive the entire chat history and character token locations.

    :message keys:
        room_id:        The id of the room which the client
                        is in.
        character_name: Doesn't actually do anything. Should be removed.
    """
    time_received = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    user_id = current_user.id
    username = current_user.username
    room_id = message['room_id']
    initiatives = read_db("active_room", "character_name, init_val, user_id", f"WHERE room_id = '{room_id}'")
    chats = read_db("chat", "username, chat", f"WHERE room_id = '{room_id}'")
    map_status = {}
    db_read = read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0]
    if db_read:
        map_status = json.loads(db_read)
    
    wrong_room = []
    for i in map_status:
        if map_status[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del map_status[i]

    add_to_db("log", (room_id, user_id, "Connection", f"User with id {user_id} connected", time_received))
    app.logger.debug(f"Battle update: User {current_user.username} has connected to room {room_id}")

    emit('log_update', {'desc': f"{username} Connected"}, room=room_id)

    your_characters = []
    character_names_read_from_db = read_db("active_room", "character_name", f"WHERE user_id='{user_id}' AND room_id='{room_id}'")
    for name in character_names_read_from_db:
        your_characters.append(name[0])
    for player_id in map_status:
        if player_id == user_id and map_status[player_id]['character_name'] not in your_characters:
            your_characters.append(map_status[player_id]['character_name'])
    for character in your_characters:
        emit('populate_select_with_character_names', {'character_name': character, 'username': current_user.username})

    for item in initiatives:
        username = read_db("users", "username", f"WHERE user_id = '{item[2]}'")[0][0]
        emit('initiative_update', {'character_name': item[0], 'init_val': item[1], 'username': username})
    emit('log_update', {'desc': "Initiative List Received"})

    for item in chats:
        emit('chat_update', {'chat': item[1], 'character_name': item[0]})
    emit('log_update', {'desc': "Chat History Received"})

    # populate the map with the character tokens
    if map_status:
        emit('redraw_character_tokens_on_map', map_status, room=room_id)
        emit('log_update', {'desc': "Character Tokens Received"})

    if read_db("active_room", "*", f"WHERE room_id = '{room_id}' AND is_turn = '1'"):
        emit('log_update', {'desc': "Combat has already started; grabbing the latest information"})

        character = read_db("active_room", "user_id, character_name", f"WHERE room_id = '{room_id}' AND is_turn = '1'")[0]
        turn_username = read_db("users", "username", f"WHERE user_id = '{character[0]}'")[0][0]

        emit('log_update', {'desc': "Rejoined Combat"}, room=room_id)
        emit('combat_connect', {'desc': 'Rejoined Combat', 'first_turn_name': character[1], 'username': turn_username})


@socketio.on('character_icon_update_database', namespace='/combat')
def character_icon_update_database(message):
    """
    The character_icon_update_database event handler. This function
    updates the information related to the specified character
    token. From here, the update is then pushed out to all connected
    clients.

    :message keys:
        desc:               Either "Change Location" or "Resize"
        character_image:    The URL to the character's picture
        username:           The username of the owner of the character
        character_name:     The name of the character
        new_top:            The new y coordinate of the top left pixel
        new_left:           The new x coordinate of the top left pixel
        new_width:          The new width of the token in pixels
        new_height:         The new height of the token in pixels
        is_turn:            Boolean stating if it is the character's turn
        room_id:            The id of the room which the token belongs
    """
    username = message['username']
    room_id = message['room_id']
    temp_read_for_user_id = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    for character in temp_read_for_user_id:
        if temp_read_for_user_id[character]['username'] == message['username'] and temp_read_for_user_id[character]['character_name'] == message['character_name']:
            user_id_character_name = character
    
    map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
    
    wrong_room = []
    for i in map_status:
        if map_status[i]['room_id'] != room_id:
            wrong_room.append(i)
    for i in wrong_room:
        del map_status[i]

    # Ensure that there is a valid value for the token position and size
    if message['new_top'] == "Null":
        new_top = map_status[user_id_character_name]['top']
    else:
        new_top = message['new_top']
    if message['new_left'] == "Null":
        new_left = map_status[user_id_character_name]['left']
    else:
        new_left = message['new_left']
    if message['new_width'] == "Null":
        new_width = map_status[user_id_character_name]['width']
    else:
        new_width = message['new_width']
    if message['new_height'] == "Null":
        new_height = map_status[user_id_character_name]['height']
    else:
        new_height = message['new_height']
        

    # TODO: Add check here to make sure that the token you're trying to move is your own and not someone elses. Check the user_id_character_name from user_id_character_name = character in the loop above against current_user.username. Add exception for if you are the DM
    json_character_to_update = { user_id_character_name: {"username": message['username'], "character_name": message['character_name'], "room_id": message['room_id'], "character_image": message['character_image'], "height": new_height, "width": new_width, "top": new_top, "left": new_left, "is_turn": message['is_turn']}}
    map_status[user_id_character_name] = json_character_to_update[user_id_character_name]
    characters_json = json.dumps(map_status)
    update_db("room_object", f"map_status = '{characters_json}'", f"WHERE active_room_id = '{room_id}'")

    if message['desc'] == "Resize":
        app.logger.debug(f"User {username} has resized their character")
    elif message['desc'] == "ChangeLocation":
        app.logger.debug(f"User {username} has moved their character to X:{message['new_left']}, Y:{message['new_top']}")
        emit('log_update', {'desc': f"{message['character_name']} moved"}, room=room_id)

    emit('redraw_character_tokens_on_map', map_status, room=room_id)


@socketio.on('add_character', namespace='/combat')
def add_character(message):
    """
    The add_character event handler. This function
    adds a specific character to the given room. It
    removes the character from the user's "Add character" select,
    adds it to their "Update initiative" select and initializes
    the character's initiative to 0.

    :message keys:
        char_name:  The name of the character being added
        username:   The username of the player who owns the character
        room_id:    The id of the room the user is in
    """
    character_name = message['char_name']
    room_id = message['room_id']
    user_id = current_user.id
    username = message['username']
    temp_db_read_character_token = read_db("characters", "char_token", f"WHERE user_id = '{user_id}' AND character_name = '{character_name}'")
    initiative = 0

    if temp_db_read_character_token:
        character_image = temp_db_read_character_token[0][0]
    else:
        # TODO: This is just a place holder for if a user does not have an image for their character - but that should never happen anyways
        character_image = "http://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Auto_Racing_Black_Box.svg/800px-Auto_Racing_Black_Box.svg.png"

    temp_db_read_init_value = read_db("active_room", "init_val", f"WHERE room_id='{room_id}' AND user_id = '{user_id}' AND character_name = '{character_name}'")
    if temp_db_read_init_value:
        initiative = temp_db_read_init_value[0][0]
    else:
        add_to_db("active_room", (room_id, user_id, character_name, 0, 0, character_image))

    emit('populate_select_with_character_names', {'character_name': character_name, 'username': username}, room=room_id)
    emit('initiative_update', {'character_name': character_name, 'init_val': initiative, 'username': username}, room=room_id)
    character_icon_add_database(character_name, username, character_image, user_id, room_id)
    app.logger.debug(f"User {username} has added character {character_name} to the battle")


@socketio.on('remove_character', namespace="/combat")
def remove_character(message):
    """
    The remove_character event handler. This function removes a specific
    character from a room. Usually this is done when a character
    dies or is accidentally added.

    :message keys:
        character_name: the character who is being removed.
        username: the owner of `character_name`
        room_id: the id the character is in
        init_val: the initiative of the character
        next_character_name: null if not the character's turn. It it exists, the name of the character who's turn it is next
        next_username: null if not the character's turn. If it exists, the owner of `next_character_name`
    """
    room_id = message['room_id']    
    username = message['username']
    character_name = message["character_name"]
    user_id = read_db("users", "user_id", f"WHERE username = '{username}'")[0][0]     # Required for the removal from the room's JSON

    if message["next_character_name"]:
        next_username = message["next_username"]
        next_character_name = message["next_character_name"]
        next_character_id = read_db("users", "user_id", f"WHERE username = '{next_username}'")[0][0]

        map_status = json.loads(read_db("room_object", "map_status", f"WHERE active_room_id = '{room_id}'")[0][0])
        
        wrong_room = []
        for i in map_status:
            if map_status[i]['room_id'] != room_id:
                wrong_room.append(i)
        for i in wrong_room:
            del map_status[i]
        previous_user_id_character_name = str(user_id) + '_' + str(character_name)
        next_user_id_character_name = str(next_character_id) + '_' + str(next_character_name)
        previous_json_character_to_update = { previous_user_id_character_name: {"username": username, "character_name": character_name, "room_id": room_id, "character_image": map_status[previous_user_id_character_name]['character_image'], "height": map_status[previous_user_id_character_name]['height'], "width": map_status[previous_user_id_character_name]['width'], "top": map_status[previous_user_id_character_name]['top'], "left": map_status[previous_user_id_character_name]['left'], "is_turn": 0}}
        next_json_character_to_update = { next_user_id_character_name: {"username": next_username, "character_name": next_character_name, "room_id": room_id, "character_image": map_status[next_user_id_character_name]['character_image'], "height": map_status[next_user_id_character_name]['height'], "width": map_status[next_user_id_character_name]['width'], "top": map_status[next_user_id_character_name]['top'], "left": map_status[next_user_id_character_name]['left'], "is_turn": 1}}
        map_status[previous_user_id_character_name] = previous_json_character_to_update[previous_user_id_character_name]
        map_status[next_user_id_character_name] = next_json_character_to_update[next_user_id_character_name]
        characters_json = json.dumps(map_status)
        update_db("room_object", f"map_status = '{characters_json}'", f"WHERE active_room_id = '{room_id}'")

        update_db("active_room", f"is_turn = '{1}'", f"WHERE room_id = '{room_id}' AND user_key = '{next_character_id}' AND character_name = '{next_character_name}'")    
    
    character_icon_del_database(character_name, username, user_id, room_id)
    delete_from_db("active_room", f"WHERE room_id = '{room_id}' and character_name = '{character_name}' and user_id = '{user_id}'")

    emit('removed_character', {"username":username, "character_name": ":".join(character_name.split("_")), "user_id":user_id, "init_val":message["init_val"]}, room=room_id)
    app.logger.debug(f"User {username} has removed character {character_name} from the battle")


@socketio.on('add_npc', namespace='/combat')
def add_npc(message):
    """
    The add_npc event handler. This function
    adds a randomized npc to the room. The npc
    is added to the client's "Update initiative"
    select and their initiative is set to 0.

    :message keys:
        username:   The username of the user who 
                    created the npc
        room_id:    The id of the room in which the
                    npc was created
    """
    room_id = message['room_id']
    user_id = current_user.id
    random_key = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
    character_name = "NPC" + random_key
    username = message['username']
    initiative = 0
    character_image = random.choice(npc_images)

    temp_db_read_init_value = read_db("active_room", "init_val", f"WHERE room_id='{room_id}' AND user_id = '{user_id}' AND character_name = '{character_name}'")
    if temp_db_read_init_value:
        init_val = temp_db_read_init_value[0][0]
    else:
        add_to_db("active_room", (room_id, user_id, character_name, 0, 0, character_image))

    emit('populate_select_with_character_names', {'character_name': character_name, 'username': username}, room=room_id)
    emit('initiative_update', {'character_name': character_name, 'init_val': initiative, 'username': username}, room=room_id)
    character_icon_add_database(character_name, username, character_image, user_id, room_id)
    app.logger.debug(f"User {username} has added character {character_name} to the battle")


"""
Error Handlers:
    These functions handle all errors that the 
    user creates. They are all have the `@app.errorhandler`
    decorator and handle their designated errors.

    All of the functions also have one parameter: `e`.
    `e` is the error object.

    The functions are as follows (list as the errors
    they handle):
        1.  CSRFError
        2.  HTTPException
        3.  Exception
"""


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """
    The CSRFError handler. This function
    grabs all of the errors related to CSRF tokens
    and loads the information into the error.html 
    template. 
    
    For the most part, this happens with 
    entering fors when the user is not logged in
    or the user somehow is able to stay in a room
    after it has been closed.
    """
    app.logger.warning(f"A CSRFError has occurred. How did this happen?")
    return render_template("error.html", error_name="Error Code 400" ,error_desc = "The room you were in has closed!", username=current_user.username), 400


@app.errorhandler(HTTPException)
def generic_error(e):
    """
    The HTTPException handler. This function handles
    all HTTP errors that are not 5xx. This handler
    deals with all user errors, such as attempting to
    connect to a route on the site that does not exist.
    """
    app.logger.warning(f"A HTTP error with code {e.code} has occurred. Handling the error.")
    return render_template("error.html", error_name=f"Error Code {e.code}", error_desc=e.description, username=current_user.username, profile_picture=current_user.profile_picture), e.code


@app.errorhandler(Exception)
def five_hundred_error(e):
    """
    The generic error handler. Technically, this handler
    deals with all errors that are not CSRFErrors or 
    HTTPExceptions. Because app.errorhandler works with more
    specific errors first, this handler will only be called
    when the error is not a CSRFError or an HTTPException.

    Because of that, this will handle any sort of server error,
    or in IP terms, 5xx errors. In terms related to use developers,
    errors that we should fix.
    """
    app.logger.warning(f"A server error occurred. Handling it, but you probably should fix the bug...")
    app.logger.error(f"Here it is: {e}")
    desc = "Internal Server Error. Congrats! You found an unexpected feature!"
    return render_template("error.html", error_name="Error Code 500", error_desc=desc, username=current_user.username, profile_picture=current_user.profile_picture), 500


@app.route("/process_error", methods=["POST"])
@login_required
def process_error():
    """
    The /process error route. This route is made for
    processing user input for errors. But lets be honest,
    who actually fills out those forms?

    Should be removed.
    """
    if 'error_desc' in request.form:
        add_to_error_db(request.form['error_desc'])
    
    return redirect(url_for("home"))


"""
App Running:
    This if statement determines how the application
    is run. If this file is run directly or through
    `flask run`, the "if" part of the application will
    run. Otherwise, when run through something else like
    nginx or gunicorn, the else block will run
"""


if __name__ == "__main__":
    app.run(ssl_context="adhoc", port=33507, debug=True)

else:
    # logging levels: info, debug, warning, critical, error
    
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(logging.DEBUG)
    # app.logger.setLevel(gunicorn_logger.level)


# --- References ---
# Google login with Flask: https://realpython.com/flask-google-login/
# Websockets: https://blog.miguelgrinberg.com/post/easy-websockets-with-flask-and-gevent 
# Gunicorn logging: https://trstringer.com/logging-flask-gunicorn-the-manageable-way/
# Random room_id generation: https://stackoverflow.com/a/30779367

# --- Developer Links ---
# Visit https://console.developers.google.com/apis/credentials/oauthclient/211539095216-3dnbifedm4u5599jf7spaomla4thoju6.apps.googleusercontent.com?project=seniorproject-294418&supportedpurview=project to get ID and SECRET, then export them in a terminal to set them as environment variables