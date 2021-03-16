import time
import hashlib
from datetime import datetime

from flask import request
from flask_security import current_user
import requests


from common.utils import serialize_dict


class LoyaltyClient:
    def create_customer(self, **params):
        pass

