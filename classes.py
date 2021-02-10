from flask_login import UserMixin, AnonymousUserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, validators, Form, FileField
from wtforms.validators import Length, NumberRange, DataRequired, ValidationError, Regexp, URL, Optional
from wtforms_validators import AlphaNumeric, AlphaSpace
import random
import string


##
## Validate that character input is valid
##


class CharacterValidation(FlaskForm):
    name = StringField('Name', [DataRequired(message="Please Input Name"), Length(min=1, max=25, message ="Bad Name Size"), AlphaSpace(message="Names must only be alphanumeric!")])
    race = StringField('Race', [DataRequired(message="Please choose a race")])
    subrace = StringField('Subrace', [DataRequired(message="Please choose a subrace")])
    speed = IntegerField('speed', [DataRequired(message="Please input Speed"), NumberRange(min=1, max=100, message="Outside Possible Range")])
    classname = StringField('class', [DataRequired(message="Please choose class ")])
    subclass = StringField('subclass', [DataRequired(message ="Please choose subclass")])
    level = IntegerField('level', [DataRequired(message="Please input level"), NumberRange(min=1, max=20, message="Outside Possible Range")])
    strength = IntegerField('Str', [DataRequired(message="Please input strength"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    dexterity = IntegerField('Dex', [DataRequired(message="Please input dex"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    constitution = IntegerField('cons', [DataRequired(message="Please input cons"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    intelligence = IntegerField('int', [DataRequired(message="Please input int"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    wisdom = IntegerField('wis', [DataRequired(message="Please input wis"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    charisma = IntegerField('chr', [DataRequired(message="Please input charisma"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    hitpoints = IntegerField('hp', [DataRequired(message="Please input hp")])
    char_token = StringField('token', [Optional(), Regexp("^https?://(?:[a-zA-Z0-9\-]+\.)+[a-z]{2,6}(?:/[^/#?]+)+\.(?:jpg|gif|png|jpeg|webp)$", message="Character token must be an image!")])


class RoomValidation(FlaskForm):
    room_name = StringField("Room", [DataRequired(message="Please input the name of your room"), Length(min=1, max=42, message="Name must be between 1 and 42 characters")])
    map_url =  StringField('Image Link', [URL(message="Image must be a valid URL"), Regexp("^https?://(?:[a-z\-]+\.)+[a-z]{2,6}(?:/[^/#?]+)+\.(?:jpg|gif|png|jpeg|webp)$", message="Encounter map must be an image!")])
    dm_notes = StringField("DM_notes", [Optional()])


class SitenameValidation(FlaskForm):
    username = StringField('Username', [DataRequired(message="You need to enter some text!"), AlphaNumeric(message="Only alphanumeric characters are allowed")])
    

class User(UserMixin):
    def __init__(self, id_, email, profile_pic, username=None):
        self.id = id_
        self.email = email
        self.profile_pic = profile_pic
        self.username = username

    # GETTERS
    def get_user_id(self):
        return self.id

    def get_email(self):
        return self.email

    def get_profile_pic(self):
        return self.profile_pic

    def get_username(self):
        return self.username

    def __repr__(self):
        return f"User({self.id}, {self.email}, {self.profile_pic}, {self.username})"



class AnonymousUser(AnonymousUserMixin):
    def __init__(self):
        self.id = ''.join(random.choice(string.digits) for _ in range(4))
        self.profile_pic = "https://i.stack.imgur.com/34AD2.jpg"
        self.username = "guest" + self.id
        
    def get_user_id(self):
        return self.id

    def get_profile_pic(self):
        return self.profile_pic
    
    def get_username(self):
        return self.username


