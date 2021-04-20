from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_security import Security


db = SQLAlchemy()
security = Security()
admin = Admin(name='Loyalty', template_mode='bootstrap3')
