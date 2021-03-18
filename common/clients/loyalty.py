import time
import hashlib
import traceback
from datetime import datetime

from flask import request
from flask_security import current_user


from common.utils import serialize_dict
from models.loyalty import Customer, ErrorLog


class LoyaltyClient:

    def create_customer(self, **params):
        try:
            Customer.create(**params)
        except Exception as ex:
            ErrorLog.create(request_data=request.data,
                            request_ip=request.remote_addr,
                            request_url=request.url,
                            request_method=request.method,
                            error=str(ex),
                            traceback=traceback.format_exc())




