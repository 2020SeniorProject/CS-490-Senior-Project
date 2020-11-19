from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, validators, Form
from wtforms.validators import Length, NumberRange, DataRequired, ValidationError



##
## Validate that character input is valid
##


class CharacterValidation(FlaskForm):
    name = StringField('Name', [DataRequired(message="Please Input Name"), Length(min=1, max=20, message ="Bad Name Size")])
    race = StringField('Race', [DataRequired(message="Please choose a race")] )
    subrace = StringField('Subrace', [DataRequired(message="Please choose a subrace")])
    speed = IntegerField('speed', [DataRequired(message="Please input Speed")])
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




class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    # GETTERS
    def get_user_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_email(self):
        return self.email

    def get_profile_pic(self):
        return self.profile_pic

    def __repr__(self):
        return f"User({self.id}, {self.name}, {self.email}, {self.profile_pic})"