from flask import session, flash
from flask_wtf import FlaskForm
from wtforms import fields as wtfields
from flask_admin.form.widgets import DatePickerWidget
# from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import InputRequired, URL, NumberRange, Optional

from models.admin import user_datastore
from models.loyalty import DiscountLevel
from models.utils import db_wrapper
from common.fields import PrettyJsonField



class CustomerCreationForm(FlaskForm):
    name = wtfields.StringField(validators=[InputRequired()])
    phone = wtfields.IntegerField(validators=[InputRequired()])
    amount_of_purchases = wtfields.IntegerField('Total amount of purchases',
                                                validators=[InputRequired(),
                                                            NumberRange(min=0)])
    birthday = wtfields.DateField(validators=[InputRequired()], widget=DatePickerWidget())
    address = wtfields.StringField(validators=[Optional()])
