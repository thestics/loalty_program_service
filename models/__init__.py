# from models.loyalty import CREATING_LIST as loyalty_tables
# from models.admin import CREATING_LIST as admin_tables
# from models.utils import db_wrapper
#
#
# def init_db():
#     try:
#         db_wrapper.connect_db()
#         db = db_wrapper.database
#         db.drop_tables(loyalty_tables + admin_tables)
#         print("tables dropped")
#         db.create_tables(loyalty_tables + admin_tables)
#         print("tables created")
#         db.close()
#     except:
#         db_wrapper.database.rollback()
#         raise
#
#
# # init_db()
