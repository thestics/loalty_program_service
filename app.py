from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_security import Security

app = Flask(__name__)
db = SQLAlchemy()
security = Security()

from models.admin import user_datastore

from views import admin as admin_views
from views import manager as manager_views
from views import cashier as cashier_views

from routes.root import root
from routes.event import create_event


app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///loyalty.db'
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_PASSWORD_SALT'] = 'test111'

db.init_app(app)
security.init_app(app, user_datastore)

admin = Admin(app, name='Loyalty', index_view=admin_views.DashboardView(), template_mode='bootstrap3')

admin.add_view(admin_views.user_view)

admin.add_view(manager_views.manager_level_view)
admin.add_view(manager_views.manager_client_view)
admin.add_view(manager_views.manager_event_view)

admin.add_view(cashier_views.cashier_client_view)
admin.add_view(cashier_views.cashier_event)

admin.add_link(admin_views.LogoutMenuLink(name='Logout', url='/logout'))

if __name__ == '__main__':
    app.run()
