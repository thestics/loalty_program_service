from playhouse.flask_utils import FlaskDB

from flask_security import PeeweeUserDatastore
from peewee import prefetch


class CustomFlaskDB(FlaskDB):
    def connect_db(self):
        # fix: explicitly close connection
        # todo: find why db doesn't close after request teardown
        self.close_db(None)
        self.database.connect()


class CustomPeeweeUserDatastore(PeeweeUserDatastore):
    def find_user(self, **kwargs):
        query = list(prefetch(
            self.user_model
                .select(self.user_model)
                .filter(**kwargs),

            self.UserRole
                .select(self.UserRole, self.role_model)
                .join(self.role_model)
        ))

        if len(query) == 0:
            return

        return query[0]


db_wrapper = CustomFlaskDB()


class BaseModel(db_wrapper.Model):
    pass


def init_db(creating_list):
    try:
        db_wrapper.connect_db()
        db = db_wrapper.database
        db.drop_tables(creating_list, cascade=True)
        print("tables dropped")
        db.create_tables(creating_list)
        print("tables created")
        db.close()
    except:
        db_wrapper.database.rollback()
        raise
