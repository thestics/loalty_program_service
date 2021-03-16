from peewee import (CharField, TextField, BooleanField, DateTimeField,
                    IntegerField, ForeignKeyField, datetime)
from playhouse.postgres_ext import BinaryJSONField
from flask_security import RoleMixin, UserMixin

from models.utils import CustomPeeweeUserDatastore, db_wrapper, BaseModel


class Role(BaseModel, RoleMixin):
    class Meta:
        db_table = 'roles'

    name = CharField(unique=True)
    description = TextField(null=True)
    permissions = BinaryJSONField(default=dict())


class User(BaseModel, UserMixin):
    class Meta:
        db_table = 'users'

    email = CharField(unique=True)
    password = CharField()
    active = BooleanField(default=True)
    last_login_at = DateTimeField(null=True)
    current_login_at = DateTimeField(null=True)
    last_login_ip = CharField(max_length=100, default='127.0.0.1')
    current_login_ip = CharField(max_length=100, default='127.0.0.1')
    login_count = IntegerField(default=0)
    allowed_ips = BinaryJSONField(null=True)
    created = DateTimeField(default=datetime.datetime.now)
    two_factor_required = BooleanField(default=False)
    two_factor_secret = CharField(null=True)

    def get_roles(self):
        return Role.select().join(UserRoles).where(UserRoles.user == self)

    def can_perform(self, view_id, action):
        for user_role in self.roles:
            if user_role.role.name in ('superuser', 'manager'):
                continue

            if (view_id in user_role.role.permissions
                    and action in user_role.role.permissions[view_id]):
                return True

        return False

    def has_access(self, view_id):
        for user_role in self.roles:
            if user_role.role.name in ('superuser', 'manager'):
                continue

            if view_id in user_role.role.permissions:
                return True

        return False

    def is_superuser(self):
        return self.has_role('superuser')

    def is_manager(self):
        return self.has_role('manager')


class UserRoles(BaseModel):
    class Meta:
        db_table = 'user_roles'

        indexes = (
            (('user', 'role',), True),
        )

    user = ForeignKeyField(User, backref='roles')
    role = ForeignKeyField(Role, backref='users')

    name = property(lambda self: self.role.name)
    description = property(lambda self: self.role.description)


user_datastore = CustomPeeweeUserDatastore(db_wrapper.database,
                                           User,
                                           Role,
                                           UserRoles)

admin_tables = (User, Role, UserRoles)
