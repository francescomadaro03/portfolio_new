from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, name, surname, email, username, u_type):
        self.name = name
        self.surname = surname
        self.email = email
        self.username = username
        self.type = u_type

    def get_id(self):
        return self.email
    
    def __repr__(self):
        return f'{self.email} - {self.username} '