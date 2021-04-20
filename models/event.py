from .admin import User
from .loyalty import Client
from datetime import datetime

from exts import db


class Events(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    closed = db.Column(db.Boolean, default=False)
    success = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)

    client_id = db.Column(db.Integer, db.ForeignKey(Client.id), nullable=False)
    client = db.relationship(Client)

    sum_before = db.Column(db.Float, nullable=False)
    sum_after = db.Column(db.Float, nullable=False)

    present_given = db.Column(db.Boolean, default=False)

    event_time = db.Column(db.DateTime, default=datetime.now())

    @classmethod
    def from_card_id(cls, user_card_id, client_card_id, sum_before):
        user = User.query.filter(User.card_id == user_card_id).first()
        client = Client.query.filter(Client.card_id == client_card_id).first()
        sum_after = client.discount(sum_before)
        return cls(user_id=user.id, client_id=client.id,
                   sum_before=sum_before, sum_after=sum_after)

    def close_success(self, present_given):
        self.client.update_balance(self.sum_after)
        if present_given:
            self.client.last_present_date = datetime.today()
        self.closed = True
        self.success = True
        db.session.add(self.client)
        db.session.add(self)

    def close_abort(self):
        self.closed = True
        self.success = False
        db.session.add(self)

    def get_form_labels(self):
        labels = (
            dict(name="Cashier card id", value=self.user.card_id),
            dict(name="Client", value=self.client.name),
            dict(name="Client card id", value=self.client.card_id),
            dict(name="Sum before discount", value=str(self.sum_before)),
            dict(name="Discount level", value=str(self.client.level)),
        )

        if self.client.vip_discount > 0:
            vip_discount = (dict(name="Vip Discount", value=str(self.client.vip_discount)), )
            labels += vip_discount

        final_sum = (dict(name="Sum after discount", value=str(self.sum_after)), )

        return labels + final_sum
