from flask_login import UserMixin

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