from datetime import datetime

from environs import Env
from pytz import timezone

env = Env()

env.read_env('/Users/involve/loalty_program_service/.env')

with env.prefixed("APP_"):
    class Config(object):
        DEBUG = False
        TESTING = False
        PROJECT = 'admin'
        SECRET_KEY = env.str("SECRET_KEY")
        TZ = 'Europe/Kiev'

        # Flask-Security config
        SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
        SECURITY_PASSWORD_SALT = env.str("SECURITY_PASSWORD_SALT")
        SECURITY_POST_LOGIN_VIEW = "/"
        SECURITY_POST_LOGOUT_VIEW = "/"
        SECURITY_REGISTERABLE = False
        SECURITY_CONFIRMABLE = False
        SECURITY_RECOVERABLE = False
        SECURITY_CHANGEABLE = False
        SECURITY_TRACKABLE = True
        SECURITY_SEND_REGISTER_EMAIL = False
        SECURITY_TWO_FACTOR = False
        SECURITY_DATETIME_FACTORY = lambda: datetime.now(timezone('Europe/Kiev'))

        FLASK_ADMIN_FLUID_LAYOUT = True

        SESSION_TIMEOUT = env.int("SESSION_TIMEOUT", 60)

        with env.prefixed("DB_"):
            DB = dict(
                engine='playhouse.postgres_ext.PostgresqlExtDatabase',
                name=env.str("NAME"),
                user=env.str("USER"),
                password=env.str("PASSWORD"),
                host=env.str("HOST"),
                port=env.int("PORT"),
                register_hstore=False,
                server_side_cursors=False,
                autorollback=True
            )

    class ProductionConfig(Config):
        ENV = 'production'


    class DevelopmentConfig(Config):
        DEBUG = True
        ENV = 'development'


    class TestingConfig(Config):
        TESTING = True

    FERNET_KEY = env.str("FERNET_KEY")
