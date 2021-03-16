from peewee import (CharField, DecimalField, ForeignKeyField,
                    BigIntegerField, DateTimeField, BooleanField, TextField,
                    DateField, datetime as peewee_datetime)
from playhouse.postgres_ext import BinaryJSONField, JSONField

from models.utils import BaseModel


class DiscountLevel(BaseModel):
    class Meta:
        db_table = "discount_levels"
        order_by = ("-created",)

    name = CharField()
    minimal_amount = DecimalField()
    created = DateTimeField(default=peewee_datetime.datetime.now)
    extra_data = BinaryJSONField(default=dict())
    processing = BooleanField(default=False, null=True)


class Customer(BaseModel):
    class Meta:
        db_table = "customers"

    name = CharField()
    phone = BigIntegerField()
    amount_of_purchases = DecimalField()
    discount_level = ForeignKeyField(DiscountLevel, default=1)
    birthday = DateField()
    address = CharField(null=True)
    family_birthdays = JSONField()
    created = DateTimeField(default=peewee_datetime.datetime.now)
    updated = DateTimeField(null=True)

    @staticmethod
    def get_for_update(wallet_id):
        return Customer.select().where(Customer.id == wallet_id).for_update().first()

    def update_balance(self, amount):
        Customer.update(balance=Customer.balance + amount).where(Customer.id == self.id).execute()


class ErrorLog(BaseModel):
    class Meta:
        db_table = "error_logs"

    request_data = BinaryJSONField()
    request_ip = CharField()
    request_url = TextField()
    request_method = CharField()
    error = TextField()
    traceback = TextField(null=True)
    created = DateTimeField(default=peewee_datetime, index=True)


loyalty_tables = (DiscountLevel, Customer, ErrorLog)
