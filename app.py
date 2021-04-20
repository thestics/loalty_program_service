from flask import Flask

from models.admin import user_datastore

from views import admin as admin_views
from views import manager as manager_views
from views import cashier as cashier_views

from exts import db, security, admin

from routes.root import root
from routes.event import create_event


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///loyalty.db'
    app.config['SECRET_KEY'] = 'mysecret'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECURITY_PASSWORD_SALT'] = 'test111'

    db.init_app(app)
    security.init_app(app, user_datastore)

    admin.init_app(app,  index_view=admin_views.DashboardView(),)
    admin.add_view(admin_views.user_view)

    admin.add_view(manager_views.manager_level_view)
    admin.add_view(manager_views.manager_client_view)
    admin.add_view(manager_views.manager_event_view)

    admin.add_view(cashier_views.cashier_client_view)
    admin.add_view(cashier_views.cashier_event)

    admin.add_link(admin_views.LogoutMenuLink(name='Logout', url='/logout'))

    app.add_url_rule('/', view_func=root, methods=['GET'])
    app.add_url_rule('/api/create_event', view_func=create_event, methods=['PUT'])

    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
