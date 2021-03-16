from flask import session, flash
from flask_wtf import FlaskForm
from wtforms import fields as wtfields
from wtforms.validators import InputRequired, URL, NumberRange, Optional

from models.admin import user_datastore
from common.fields import PrettyJsonField


class InvoiceCreationForm(FlaskForm):
    secret_key = wtfields.StringField(validators=[InputRequired()])
    partner_id = wtfields.StringField(validators=[InputRequired()])
    partner_invoice_id = wtfields.StringField(validators=[InputRequired()])
    payout_address = wtfields.StringField(validators=[InputRequired()])
    callback = wtfields.StringField('Callback URL',
                                    validators=[InputRequired(), URL()])
    confirmations_trans = wtfields.IntegerField(
        'Number of transit confirmations', validators=[Optional(),
                                                       NumberRange(min=1)])
    confirmations_payout = wtfields.IntegerField(
        'Number of payout confirmations', validators=[Optional(),
                                                      NumberRange(min=1)])
    fee_level = wtfields.SelectField(choices=(('', 'None'),
                                              ('low', 'Low'),
                                              ('medium', 'Medium'),
                                              ('high', 'High')))


class CustomerCreationForm(FlaskForm):
    name = wtfields.StringField(validators=[InputRequired()])
    phone = wtfields.IntegerField(validators=[InputRequired()])
    amount_of_purchases = wtfields.IntegerField('Total amount of purchases',
                                                validators=[InputRequired(),
                                                            NumberRange(min=0)])
    discount_level = wtfields.IntegerField(validators=[InputRequired()])
    birthday = wtfields.DateField(validators=[InputRequired()])
    address = wtfields.StringField(validators=[Optional()])
    family_birthdays = PrettyJsonField(validators=[Optional()])
