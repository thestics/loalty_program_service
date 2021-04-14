from flask_admin.contrib.sqla.view import ModelView, func
from flask_admin import expose
from flask_admin.form import rules
from flask_admin.model.template import EndpointLinkRowAction
from flask_security import current_user
from flask import redirect, request, flash
from wtforms import BooleanField, SubmitField, validators
from flask_wtf import FlaskForm

import models.loyalty as loyalty_models
import models.event as event_models
from __main__ import db


class CashierClientView(ModelView):

    can_create = True
    can_edit = True
    can_delete = False

    column_list = (
        'name',
        'card_id',
        'level',
        'vip_discount',
    )

    form_excluded_columns = (
        'level',
        'balance',
        'vip_discount',
        'last_present_date'
    )

    form_edit_rules = [
        rules.FieldSet(('card_id',), 'New card')
    ]

    form_args = dict(
        card_id=dict(
            validators=[
                validators.Length(min=10, max=10),
                validators.DataRequired()
            ]
        ),
        name=dict(
            validators=[
                validators.Length(max=255),
                validators.DataRequired(),
                validators.Regexp(r"[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+", message='Invalid characters occurred')
            ]
        ),
        phone=dict(
            validators=[
                validators.DataRequired(),
                validators.Regexp(r"\+\d{12}", message="Should be like '+380000000000'")
            ]
        ),
        birth_date=dict(
            validators=[
                validators.DataRequired()
            ]
        )
    )

    def is_accessible(self):
        return current_user.is_active and \
               current_user.is_authenticated and \
               current_user.has_role('cashier')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect('/')


class CashierPurchaseForm(FlaskForm):
    submit = SubmitField('Submit')
    abort = SubmitField('Abort')
    present_given = BooleanField('Present Given', default=False)


class CashierEvent(ModelView):
    can_edit = False
    can_create = False
    can_delete = False
    column_display_pk = True

    column_default_sort = (
        'event_time'
    )

    column_list = (
        'id',
        'client',
        'sum_before',
        'sum_after',
        'event_time'
    )

    column_extra_row_actions = [
        EndpointLinkRowAction('glyphicon glyphicon-shopping-cart', 'events.purchase'),
    ]

    def get_query(self):
        return self.session.query(self.model).filter(
            (self.model.user_id == current_user.id) & (~self.model.closed))

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(
            (self.model.user_id == current_user.id) & (~self.model.closed))

    def is_accessible(self):
        return current_user.is_active and\
               current_user.is_authenticated and\
               current_user.has_role('cashier')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect('/')

    @expose("/admin/purchase/event", methods=('POST', 'GET'))
    def purchase(self):

        event_id = request.args.get('id')
        event = event_models.Events.query.filter_by(id=event_id).first()
        form = CashierPurchaseForm()

        if not (current_user.has_role('cashier') and current_user.id == event.user_id):
            return redirect('/admin/events')

        if request.method == 'GET':
            return self.render('purchase.html', form=form,
                                labels=event.get_form_labels(), need_present=event.client.need_present())

        if request.method == 'POST':
            if form.validate_on_submit():
                if form.submit.data:
                    event.close_success(form.present_given.data)
                    flash('Purchase was successful.', category='success')
                elif form.abort.data:
                    event.close_abort()
                    flash('Purchase aborted.', category='error')
                db.session.commit()
            return redirect('/admin/events')


cashier_client_view = CashierClientView(loyalty_models.Client, db.session, name='Create Client',
                                        endpoint='cashier_clients')

cashier_event = CashierEvent(event_models.Events, db.session, name='Purchase', endpoint='events')
