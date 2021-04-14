from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask import redirect

from wtforms import validators

import models.loyalty as loyalty_models
from models.event import Events
from __main__ import db


class ManagerLevelView(ModelView):

    form_args = dict(
        name=dict(
            validators=[
                validators.DataRequired(),
                validators.Length(max=255)
            ]
        ),
        discount=dict(
            validators=[
                validators.DataRequired(),
                validators.NumberRange(min=0, max=100, message="Discount should be from 0 to 100")
            ]
        ),
        min_balance=dict(
            validators=[
                validators.DataRequired(),
                validators.NumberRange(min=0, message='Balance should be positive')
            ]
        )
    )

    def is_accessible(self):
        return current_user.is_active and\
               current_user.is_authenticated and\
               current_user.has_role('manager')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect('/')


class ManagerClientsView(ModelView):
    can_create = False
    can_delete = False

    form_args = dict(
        vip_discount=dict(
            validators=[
                validators.DataRequired(),
                validators.NumberRange(min=0, max=100, message="Discount should be from 0 to 100")
            ]
        )
    )

    form_excluded_columns = (
        'level',
        'card_id',
        'name',
        'phone',
        'birth_date',
        'balance',
        'last_present_date'
    )

    def is_accessible(self):
        return current_user.is_active and\
               current_user.is_authenticated and\
               current_user.has_role('manager')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect('/')


class ManagerEventView(ModelView):
    can_edit = False
    can_delete = False
    can_create = False

    column_list = (
        'user',
        'client',
        'sum_before',
        'sum_after',
        'present_given'
    )

    def is_accessible(self):
        return current_user.is_active and\
               current_user.is_authenticated and\
               current_user.has_role('manager')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect('/')


manager_level_view = ManagerLevelView(loyalty_models.Levels, db.session)
manager_client_view = ManagerClientsView(loyalty_models.Client, db.session, name='Manage Clients',
                                         endpoint='manager_clients')
manager_event_view = ManagerEventView(Events, db.session, name='View events', endpoint='manager_events')
