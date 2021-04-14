from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_admin.menu import MenuLink
from flask_security import current_user
from flask import redirect

from wtforms import validators, fields

import models.admin as admin_models
from __main__ import db


class UserView(ModelView):

    form_extra_fields = dict(
        password=fields.PasswordField(validators=(validators.length(min=10, max=255), validators.DataRequired())),
        password_validation=fields.PasswordField(
            validators=(validators.EqualTo('password', message='Passwords does not match.'),)
        )
    )

    form_args = dict(
        email=dict(
            validators=[validators.Email(), validators.Length(max=255), validators.DataRequired()]
        ),
        roles=dict(
            validators=[validators.DataRequired()]
        ),
        card_id=dict(
            validators=[validators.DataRequired(), validators.Length(min=10, max=10)]
        )
    )

    column_list = (
        'email',
        'card_id',
        'roles',
        'active'
    )

    column_filters = column_list

    form_edit_rules = ('active', )
    form_create_rules = ('roles', 'email', 'card_id', 'password', 'password_validation',)

    def on_model_change(self, form, model, is_created):
        model.set_password(form.data['password'])
        model.active = True

    def is_accessible(self):
        return current_user.is_active and\
               current_user.is_authenticated and\
               current_user.has_role('superuser')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect('/')


class DashboardView(AdminIndexView):
    def is_visible(self):
        # This view won't appear in the menu structure
        return False

    def is_accessible(self):
        return current_user.is_active and\
               current_user.is_authenticated

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect('/')


class LogoutMenuLink(MenuLink):
    def is_accessible(self):
        return current_user.is_authenticated


user_view = UserView(admin_models.User, db.session)
