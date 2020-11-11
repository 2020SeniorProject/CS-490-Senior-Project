from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import Length, NumberRange, DataRequired, ValidationError


##
## Validate that initative input is valid
##

class init_validator(FlaskForm):
    player_name = StringField('Player Name', [DataRequired(message="Invalid: Please Input name"), Length(max=20, message="Invalid Name exceeds Max")])
    initiative_roll = IntegerField('Initiative Roll', [DataRequired(message="Please enter initiative roll"), NumberRange(min=0, max=50, message="Invalid: Initiative outside of range")])
    submit = SubmitField("Set Initiative")


class chr_valid(FlaskForm):
    name = StringField('Name', [DataRequired(message="Please Input Name"), Length(min=1, max=20, message ="Bad Name Size")])
    race = StringField('Race', [DataRequired(message="Please choose a race")] )
    subrace = StringField('Subrace', [DataRequired(message="PLease choose a subrace")])
    speed = IntegerField('speed', [DataRequired(message="PLease input Speed")])
    classname = StringField('class', [DataRequired(message="Please choose class ")])
    subclass = StringField('subclass', [DataRequired(message ="Please choose subclass")])
    level = IntegerField('level', [DataRequired(message="Please input level")])
    strength = IntegerField('Str', [DataRequired(message="Please input strength")])
    dexterity = IntegerField('Dex', [DataRequired(message="Please input dex")])
    constitution = IntegerField('cons', [DataRequired(message="Please input cons")])
    intelligence = IntegerField('int', [DataRequired(message="Please input int")])
    wisdom = IntegerField('wis', [DataRequired(message="Please input int")])
    charisma = IntegerField('chr', [DataRequired(message="Please input charisma")])
    hitpoints = IntegerField('hp', [DataRequired(message="Please input hp")])




