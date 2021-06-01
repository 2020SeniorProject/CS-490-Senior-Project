from flask_mongoengine import MongoEngine


db = MongoEngine()


# TODO add validators
class UserObject(db.Document):
    user_id = db.StringField()
    email = db.StringField()
    profile_pic = db.StringField()
    username = db.StringField()


# TODO add validators
class Character(db.Document):
    user_id = db.StringField()
    name = db.StringField()
    stats = db.ListField(db.IntField(), max_length=6)
    classes = db.ListField(db.ListField(db.StringField()))
    race = db.ListField(db.StringField())
    hitpoints = db.IntField()
    level = db.IntField()
    speed = db.IntField()
    char_token = db.StringField()

# TODO add validators
class RoomObject(db.Document):
    user_id = db.StringField()
    room_name = db.StringField()
    description = db.StringField()
    map_url = db.StringField()
    active_rooms = db.ListField(db.StringField())
    initial_map_status = db.DictField()


class ActiveRoom(db.Document):
    user_id = db.StringField()
    room_id = db.StringField()
    map_status = db.DictField()
    log = db.ListField(db.ListField(db.StringField()))
    chat = db.ListField(db.ListField(db.StringField()))









