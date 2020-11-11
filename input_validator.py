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







