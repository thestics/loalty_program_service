from environs import Env
import logging


env = Env()

env.read_env()

with env.prefixed("APP_"):
    with env.prefixed("LOG_"):
        LOG_TO = env.str("TO")
        LOGGER = dict(level=logging.getLevelName(env.str("LEVEL", "INFO")),
                      formatter=logging.Formatter(
                          env.str("FORMAT",
                                  "%(asctime)s [%(thread)d:%(threadName)s] [%(levelname)s] - %(name)s:%(message)s"), ),
                      file='discounter.log',
                      peewee_file='peewee.log'
                      )
    with env.prefixed("DB_"):
        DB_CONFIG = dict(
            database=env.str("NAME"),
            user=env.str("USER"),
            password=env.str("PASSWORD"),
            host=env.str("HOST"),
            port=env.int("PORT"),
            autorollback=True,
        )

    class BaseConfig(object):
        PROJECT = "discounter-py"
        DEBUG = False
        TESTING = False
        SECRET_KEY = env.str("SECRET_KEY")


    class TestConfig(BaseConfig):
        DEBUG = True
        TESTING = True
        PRESERVE_CONTEXT_ON_EXCEPTION = False
        WTF_CSRF_ENABLED = False

    TIMESTAMP_DELTA_SEC = env.int("TIMESTAMP_DELTA_SEC", 15)

    THREADS_COUNT = env.int("THREADS_COUNT", 10)

    DEFAULT_DISCOUNT_LEVEL_ID = env.int("DEFAULT_DISCOUNT_LEVEL_ID", 1)
