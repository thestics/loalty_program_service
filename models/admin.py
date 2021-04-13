from __main__ import db
from flask_security import RoleMixin, UserMixin, SQLAlchemyUserDatastore
from flask_security.utils import hash_password


class Roles(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)

    def __repr__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.String(10), unique=True, index=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255), nullable=False)

    roles = db.relationship('Roles', secondary='roles_users', backref=db.backref('users', lazy='dynamic'))

    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"{self.email}: {self.roles}"

    def set_password(self, password):
        self.password = hash_password(password)


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('roles.id')))

user_datastore = SQLAlchemyUserDatastore(db, User, Roles)
