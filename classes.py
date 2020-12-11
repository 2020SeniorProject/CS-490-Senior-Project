from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, validators, Form, FileField
from wtforms.validators import Length, NumberRange, DataRequired, ValidationError, Regexp, URL, Optional
from wtforms_validators import AlphaNumeric


##
## Validate that character input is valid
##


class CharacterValidation(FlaskForm):
    name = StringField('Name', [DataRequired(message="Please Input Name"), Length(min=1, max=20, message ="Bad Name Size")])
    race = StringField('Race', [DataRequired(message="Please choose a race")] )
    subrace = StringField('Subrace', [DataRequired(message="Please choose a subrace")])
    speed = IntegerField('speed', [DataRequired(message="Please input Speed"), NumberRange(min=1, max=100, message="Outside Possible Range")])
    classname = StringField('class', [DataRequired(message="Please choose class ")])
    subclass = StringField('subclass', [DataRequired(message ="Please choose subclass")])
    level = IntegerField('level', [DataRequired(message="Please input level"), NumberRange(min=1, max=20, message="Outside Possible Range")])
    strength = IntegerField('Str', [DataRequired(message="Please input strength"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    dexterity = IntegerField('Dex', [DataRequired(message="Please input dex"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    constitution = IntegerField('cons', [DataRequired(message="Please input cons"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    intelligence = IntegerField('int', [DataRequired(message="Please input int"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    wisdom = IntegerField('wis', [DataRequired(message="Please input int"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    charisma = IntegerField('chr', [DataRequired(message="Please input charisma"), NumberRange(min=1, max=30, message="Outside Possible Range")])
    hitpoints = IntegerField('hp', [DataRequired(message="Please input hp")])


class RoomValidation(FlaskForm):
    room_name = StringField("Room", [DataRequired(message="Please input the name of your room"), Length(min=1, max=42, message="Name must be between 1 and 42 characters")])
    # TODO: Check for valid image link? and add tokens
    map_url =  StringField('Image Link', [URL(message="Image must be a valid URL")])
    # [validators.Regexp('^\w+$\.(gif|jpe?g|tiff?|png|webp|bmp)$/i')]
    dm_notes = StringField("DM_notes", [Optional()])


# def check_char():
#     def _check_char(form, field):
#         semicolon_check = field.data.split(';')
#         if len(semicolon_check) != 1:
#             raise ValidationError("';' are not allowed in usernames")
#         space_check = field.data.split(' ')
#         if len(space_check) != 1:
#             raise ValidationError("Spaces are not allowed in usernames")
#     return _check_char

class SitenameValidation(FlaskForm):
    site_name = StringField('Username', [DataRequired(message="You need to enter some text!"), AlphaNumeric(message="Only alphanumeric characters are allowed")])
    

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic, site_name=None):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.site_name = site_name

    # GETTERS
    def get_user_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_email(self):
        return self.email

    def get_profile_pic(self):
        return self.profile_pic

    def get_site_name(self):
        return self.site_name

    def __repr__(self):
        return f"User({self.id}, {self.name}, {self.email}, {self.profile_pic}, {self.site_name})"