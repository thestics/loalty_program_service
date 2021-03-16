import datetime

from flask import Flask, url_for, session, flash, redirect
from flask_security import Security
from flask_security.core import _context_processor
from flask_admin import Admin, helpers as admin_helpers

from models.admin import user_datastore, admin_tables
from models.loyalty import loyalty_tables, DiscountLevel
from models.utils import db_wrapper, init_db
from config import ProductionConfig, DevelopmentConfig
from src.login import CustomLoginForm, create_blueprint
from src.views import init_views, IndexView
from common.utils import camel2snake

security = Security()
databases = (db_wrapper,)

admin = Admin(base_template='admin/custom_master.html',
              template_mode='bootstrap3',
              index_view=IndexView(url='/'))


def create_app(config=None,
               perform_views_init=True,
               perform_context_init=True):
    config = config or ProductionConfig

    app = Flask(config.PROJECT, instance_relative_config=True)

    app.config.from_object(config)

    app.config['DATABASE'] = app.config['DB']
    db_wrapper.init_app(app)
    # init_db(admin_tables + loyalty_tables)

    sec = security.init_app(app,
                            datastore=user_datastore,
                            login_form=CustomLoginForm,
                            register_blueprint=False)
    app.register_blueprint(create_blueprint(sec, __name__))
    app.context_processor(_context_processor)

    admin.init_app(app)

    if perform_views_init:
        init_views(admin)

    if perform_context_init:
        _init_context_processors(app, admin, sec)

    return app


def _init_context_processors(app, admin, security):
    @security.context_processor
    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
            get_url=url_for
        )

    @app.context_processor
    def app_context_processors():
        return dict(
            camel2snake=camel2snake,
            hasattr=hasattr
        )

    session_lifetime = datetime.timedelta(minutes=app.config['SESSION_TIMEOUT'])

    @app.before_request
    def make_session_permanent():
        session.permanent = True
        app.permanent_session_lifetime = session_lifetime

    # @app.errorhandler(Exception)
    # def handle_exceptions(exc):
    #     flash('Unexpected error: {}'.format(exc), 'error')
    #
    #     return redirect(url_for('admin.index'))

    # open db connections
    @app.before_request
    def _db_connection():
        for db in databases:
            if db.database.is_closed():
                db.database.connect()

    # close db connections
    @app.teardown_request
    def _db_close(exc):
        for db in databases:
            if not db.database.is_closed():
                db.database.close()


if __name__ == '__main__':
    app = create_app(DevelopmentConfig)
    app.run()
