from flask_login import UserMixin
from bson import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.name = user_data['name']
        self.faculty = user_data.get('faculty', '')
        self.department = user_data.get('department', '')
        self.role = user_data.get('role', 'user')
        self.email_verified = user_data.get('email_verified', False)
        self.verification_token = user_data.get('verification_token')
        self.date_created = user_data.get('date_created')
    
    def has_role(self, role_name):
        return self.role == role_name
    
    def is_admin(self):
        return self.role == 'admin'