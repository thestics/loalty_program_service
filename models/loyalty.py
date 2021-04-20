from exts import db
from datetime import datetime
from settings import constants


class Levels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    discount = db.Column(db.Float, nullable=False, default=0,
                        comment="Discount percent. Should be in range [0, 100)")
    min_balance = db.Column(db.Float, nullable=False, default=0,
                            comment="Minimum balance needed to acquire this discount.")

    def __repr__(self):
        return f"{self.name}: {self.discount}%"


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.String(10), nullable=False, unique=True, index=True)

    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(13), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    balance = db.Column(db.Float, default=0)

    level_id = db.Column(db.Integer, db.ForeignKey(Levels.id), nullable=False, default=1)
    level = db.relationship(Levels)

    vip_discount = db.Column(db.Float, nullable=False, default=0,
                             comment="Discount multiplier. Should be in range [0, 100)")

    last_present_date = db.Column(db.Date, nullable=False, default=datetime(2000, 1, 1))

    def __repr__(self):
        return self.name

    def update_balance(self, amount):
        self.balance += amount
        self.level = Levels.query.filter(self.balance >= Levels.min_balance).order_by(Levels.min_balance.desc()).first()

    def discount(self, amount):
        base_discount = amount - amount * self.level.discount / 100
        vip_discount = base_discount - base_discount * self.vip_discount / 100
        return vip_discount

    def need_present(self):
        bd_current_year = self.birth_date.replace(year=datetime.now().year)
        if abs((datetime.date(datetime.today()) - bd_current_year).days) < constants.PRESENT_DAYS_OFFSET:
            return self.last_present_date.year < datetime.today().year
        return False