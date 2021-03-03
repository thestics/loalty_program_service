import os
from functools import wraps
from logging.handlers import WatchedFileHandler

from flask_security import RoleMixin, UserMixin
from peewee import (Model, CharField, DateTimeField, ForeignKeyField, datetime as peewee_datetime,
                    IntegerField, DoubleField, TextField, BooleanField)
from playhouse.postgres_ext import ArrayField, BinaryJSONField, PostgresqlExtDatabase

from config import DB_CONFIG, LOG_TO, LOGGER, DEFAULT_DISCOUNT_LEVEL_ID
from utils import Logger

pw_fh = WatchedFileHandler(os.path.join(LOG_TO, LOGGER['peewee_file']))
pw_fh.setLevel(LOGGER['level'])
pw_fh.setFormatter(LOGGER['formatter'])

peewee_log = Logger(pw_fh, "peewee")

peewee_now = peewee_datetime.datetime.now

db = PostgresqlExtDatabase(**DB_CONFIG)
db.commit_select = True
db.autorollback = True


def open_db_connection():
    if db.is_closed():
        db.connect()


def close_db_connection():
    if not db.is_closed():
        db.close()


def db_connect_wrapper(func):
    """
    connect to db and disconnect from it

    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            open_db_connection()
            return func(*args, **kwargs)
        finally:
            close_db_connection()

    return wrapper


def get_base_discount_level():
    return DiscountLevel.get_by_id(DEFAULT_DISCOUNT_LEVEL_ID)


class _Model(Model):
    class Meta:
        database = db

    def __repr__(self):
        return "{class_name}(id={id})".format(class_name=self.__class__.__name__, id=self.id)

    @classmethod
    def get_by_id(cls, id):
        try:
            return cls.get(cls.id == id)
        except cls.DoesNotExist:
            return None


class DiscountLevel(_Model):
    class Meta:
        db_table = "discount_levels"
        order_by = ("-created",)

    level_id = IntegerField(index=True, primary_key=True)
    name = CharField()
    minimal_amount = DoubleField()
    created = DateTimeField(default=peewee_datetime.datetime.now)
    partner_order_id = CharField(index=True, null=True)
    extra_data = BinaryJSONField(default=dict)
    processing = BooleanField(default=False, null=True)


class Role(_Model, RoleMixin):
    class Meta:
        db_table = 'roles'

    name = CharField(unique=True)
    description = TextField(null=True)
    permissions = BinaryJSONField(default=dict())


class User(_Model, UserMixin):
    class Meta:
        db_table = "users"

    name = CharField()
    phone = IntegerField()
    amount_of_purchases = DoubleField()
    role = ForeignKeyField(Role, backref='users')
    discount_level = ForeignKeyField(DiscountLevel, default=get_base_discount_level())
    birthday = DateTimeField()
    address = CharField(null=True)
    family_birthdays = ArrayField()
    created = DateTimeField(default=peewee_datetime.datetime.now)
    updated = DateTimeField(null=True)

    @staticmethod
    def get_for_update(wallet_id):
        return User.select().where(User.id == wallet_id).for_update().first()

    def update_balance(self, amount):
        User.update(balance=User.balance + amount).where(User.id == self.id).execute()


class ErrorLog(_Model):
    class Meta:
        db_table = "error_logs"

    request_data = BinaryJSONField()
    request_ip = CharField()
    request_url = TextField()
    request_method = CharField()
    error = TextField()
    traceback = TextField(null=True)
    created = DateTimeField(default=peewee_now, index=True)


CREATING_LIST = [DiscountLevel, User, ErrorLog]


def init_db():
    try:
        db.connect()
        db.drop_tables(CREATING_LIST)
        print("tables dropped")
        db.create_tables(CREATING_LIST)
        print("tables created")
        db.close()
    except:
        db.rollback()
        raise
