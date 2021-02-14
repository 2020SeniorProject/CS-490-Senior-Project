from flask_login import UserMixin, AnonymousUserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, validators, Form, FileField
from wtforms.validators import Length, NumberRange, DataRequired, ValidationError, Regexp, URL, Optional
from wtforms_validators import AlphaNumeric, AlphaSpace
import random
import string


class CharacterValidation(FlaskForm):
    """
    The CharacterValidation class. This class is an extension
    of flask_wtf's FlaskForm class. It is called whenever a
    user attempts to create or edit a character.

    There are 15 fields total, and each have the following format:
    html_name = type_of_field('name', [validators])
    """
    name = StringField('Name', [DataRequired(message="Your character must have a name! Please insert a name."), Length(min=1, max=25, message ="Character names can be at most 25 characters. Please shorten the name"), AlphaSpace(message="Character name can only have letters and spaces. Please change your name to fit these requirements.")])
    race = StringField('Race', [DataRequired(message="Your character must have a race! Please choose a race.")])
    subrace = StringField('Subrace', [DataRequired(message="Your character must have a subrace! Please choose a subrace.")])
    speed = IntegerField('Speed', [DataRequired(message="Your character must have a speed! Please enter your character's speed."), NumberRange(min=1, max=1000, message="Your character's speed is outside the accepted range. Speed must be between 1 and 1000 feet.")])
    classname = StringField('Class', [DataRequired(message="Your character must have a class! Please choose a class.")])
    subclass = StringField('Subclass', [DataRequired(message ="Your character must have a subclass! Please choose a subclass. If your character has not yet reached a level where they choose a subclass, simple select the subclass you plan on using!")])
    level = IntegerField('Level', [DataRequired(message="Your character must have a level! Please insert the level."), NumberRange(min=1, max=20, message="A character's level must be between 1 and 20. Please enter a number within that range.")])
    strength = IntegerField('Strength', [DataRequired(message="Your character must have a strength score! Please enter your strength."), NumberRange(min=1, max=30, message="A character's strength must be between 1 and 30. Please enter a number within that range.")])
    dexterity = IntegerField('Dexterity', [DataRequired(message="Your character must have a dexterity score! Please enter your dexterity."), NumberRange(min=1, max=30, message="A character's dexterity must be between 1 and 30. Please enter a number within that range.")])
    constitution = IntegerField('Constituion', [DataRequired(message="Your character must have a constitution score! Please enter your constitution."), NumberRange(min=1, max=30, message="A character's constitution must be between 1 and 30. Please enter a number within that range.")])
    intelligence = IntegerField('Intelligence', [DataRequired(message="Your character must have a intelligence score! Please enter your intelligence."), NumberRange(min=1, max=30, message="A character's intellignece must be between 1 and 30. Please enter a number within that range.")])
    wisdom = IntegerField('Wisdom', [DataRequired(message="Your character must have a wisdom score! Please enter your wisdom."), NumberRange(min=1, max=30, message="A character's strength must be wisdom 1 and 30. Please enter a number within that range.")])
    charisma = IntegerField('Charisma', [DataRequired(message="Your character must have a charisma score! Please enter your charisma."), NumberRange(min=1, max=30, message="A character's charisma must be between 1 and 30. Please enter a number within that range.")])
    hitpoints = IntegerField('Hitpoints', [DataRequired(message="Your character must have health! Please enter your hit points.")])
    character_token = StringField('Character Token', [Optional(), Regexp("^https?://(?:[a-zA-Z0-9\-]+\.)+[a-z]{2,6}(?:/[^/#?]+)+\.(?:jpg|gif|png|jpeg|webp)$", message="A character's token must be an image. Ensure that the URL you entered ends with .jpg, .gif, .png, .jpeg or .webp!")])


class RoomValidation(FlaskForm):
    """
    The RoomValidation class. This class is an extension
    of flask_wtf's FlaskForm class. It is called whenever
    a user attempts to create or edit a room.

    There are 3 fields total, and each have the following format:
    html_name = type_of_field('name', [validators])
    """
    room_name = StringField("Room", [DataRequired(message="You room must have a name! Please input the name of your room"), Length(min=1, max=42, message="The room's name can be at most 42 characters. Please shorten the name to fit this requirement.")])
    map_url =  StringField('Image Link', [URL(message="The map must be an image with a valid URL. Please ensure that you enter a URL that exists."), Regexp("^https?://(?:[a-z\-]+\.)+[a-z]{2,6}(?:/[^/#?]+)+\.(?:jpg|gif|png|jpeg|webp)$", message="The encounter map must be an image! Please ensure that the URL you entered ends with .jpg, .gif, .png, .jpeg or .webp!")])
    dm_notes = StringField("DM Notes", [Optional()])


class UsernameValidation(FlaskForm):
    """
    The UsernameValidation class. This class is an extension
    of flask_wtf's FlaskForm class. It is called whenever a
    user initially sets or updates their username.

    There is 1 field, with the folloing format:
    html_name = type_of_field('name', [validators])
    """
    username = StringField('Username', [DataRequired(message="You must enter something for your username. Please type your username, then resubmit the form."), AlphaNumeric(message="Usernames must be alphanumeric. Please ensure that your username only uses letters and numbers.")])
    

class User(UserMixin):
    """
    The User class. This class is an extension of
    flask_login's UserMixin class and is called
    whenever a user interacts with the backend.
    """
    def __init__(self, id_, email, profile_picture, username=None):
        """
        :param id_:
            A string representation of a user's Google ID.
            This variable is actually a constant. The only
            way to change it is to completely remove a user
            from the database.
        :param email:
            A string representation of a user's Google email.
            Like the id, this variable too is a constant, and
            can only be changed by completely removing a user.
        :param profile_picture:
            A string URL of the specified email's profile 
            picture. This variable can be changed. However, the
            change must occur on the Google account.
        :param username:
            A string representation of the user's username.
            By default, when a new user first connects to
            the site, it is None until they set their username.
        """
        self.id = id_
        self.email = email
        self.profile_picture = profile_picture
        self.username = username

    
    def __getitem__(self, name):
        """
        Default getter method. Returns the value of the
        specified property.

        :param name:
            The name of the property being accessed
        """
        return self.name


    def __setitem__(self, name, value):
        """
        Default setter method. Returns a TypeError
        as the properties are pull from the database.
        Any update to the instance would not be saved.

        :param name:
            The name of the property being accessed
        :param value:
            The 'new' value of the property
        """
        return TypeError("User properties cannot be set via an instance. Update the database values instead.")


    def __repr__(self):
        """
        The string representation of a User instance
        when sent through the print() function.
        """
        return f"User({self.id}, {self.email}, {self.profile_picture}, {self.username})"


class AnonymousUser(AnonymousUserMixin):
    """
    The AnonymousUser class. This class is an
    extension of flask_login's AnonymousUserMixin
    class and is called whenever a unlogged user
    interacts with the backend.
    """
    def __init__(self):
        """
        The initilization method of anonymous users.

        This class has the same properties as the User
        class. However, all values here are preset or
        randomized, and cannot be changed by the user.
        """
        self.id = ''.join(random.choice(string.digits) for _ in range(4))
        self.profile_picture = "https://i.stack.imgur.com/34AD2.jpg"
        self.username = "guest" + self.id
        self.email = None


    def __getitem__(self, name):
        """
        Default getter method. Returns the value of the
        specified property.

        :param name:
            The name of the property being accessed
        """
        return self.name
        

    def __setitem__(self, name, value):
        """
        Default setter method. Returns a TypeError
        as the properties of an anonymous user as random
        and have no meaning.

        :param name:
            The name of the property being accessed
        :param value:
            The 'new' value of the property
        """
        return TypeError("AnonymousUser properties cannot be updated.")


    def __repr__(self):
        """
        The string representation of a User instance
        when sent through the print() function.
        """
        return f"AnonymousUser({self.id}, {self.email}, {self.profile_picture}, {self.username})"