import hmac
import hashlib
import base64
import random
import time
import json
from decimal import Decimal
from datetime import datetime
from string import ascii_uppercase, ascii_lowercase, ascii_letters, digits

from cryptography.fernet import Fernet

from config import FERNET_KEY



BASE_58_SYMBOLS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def camel2snake(string):
    return '_'.join(word.lower() for word in string.split())


def snake2camel(string):
    return ' '.join(word.capitalize() for word in string.split('_'))


class OTP:
    def __init__(self, interval, secret):
        self.interval = interval
        self.secret = secret
        self.digits = 6

    def _generate_otp(self, inp):
        """
        @param [Integer] input the number used seed the HMAC
        Usually either the counter, or the computed integer
        based on the Unix timestamp
        """
        hmac_hash = hmac.new(
            self._byte_secret(),
            self._int_to_bytestring(inp),
            hashlib.sha1,
        ).digest()

        hmac_hash = bytearray(hmac_hash)
        offset = hmac_hash[-1] & 0xf
        code = ((hmac_hash[offset] & 0x7f) << 24 |
                (hmac_hash[offset + 1] & 0xff) << 16 |
                (hmac_hash[offset + 2] & 0xff) << 8 |
                (hmac_hash[offset + 3] & 0xff))
        str_code = str(code % 10 ** self.digits)
        while len(str_code) < self.digits:
            str_code = '0' + str_code

        return str_code

    def _byte_secret(self):
        missing_padding = len(self.secret) % 8
        if missing_padding != 0:
            self.secret += '=' * (8 - missing_padding)
        return base64.b32decode(self.secret, casefold=True)

    def _int_to_bytestring(self, i, padding=8):
        """
        Turns an integer to the OATH specified
        bytestring, which is fed to the HMAC
        along with the secret
        """
        result = bytearray()
        while i != 0:
            result.append(i & 0xFF)
            i >>= 8

        return bytearray(reversed(result)).rjust(padding, b'\0')

    def get_code(self):
        for_time = int(time.time())
        return self._generate_otp(int(for_time / self.interval))


def get_random_string(choices, length, weights=None):
    return "".join(
        random.choices(
            choices,
            weights=weights,
            k=length
        )
    )


def generate_password():
    return ''.join(random.sample(
        get_random_string(ascii_letters + digits, length=7) +
        get_random_string(ascii_lowercase, length=2) +
        get_random_string(ascii_uppercase, length=2) +
        get_random_string(digits, length=2) +
        get_random_string("#$%&*+-:;<=>?@{|}~[]_~", length=2),
        15
    ))


def get_base_58_string(length):
    return ''.join([random.choice(BASE_58_SYMBOLS) for _ in range(length)])


class CustomJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return str(obj)

        return super(CustomJsonEncoder, self).default(obj)


def serialize_dict(dikt):
    return json.loads(json.dumps(dikt, cls=CustomJsonEncoder))


def decrypt_data(data):
    fernet_key = base64.urlsafe_b64encode(hashlib.md5(FERNET_KEY.encode()).hexdigest().encode())
    f = Fernet(fernet_key)
    decrypted_data = f.decrypt(data.encode()).decode()
    return decrypted_data


def encrypt_data(data):
    fernet_key = base64.urlsafe_b64encode(hashlib.md5(FERNET_KEY.encode()).hexdigest().encode())
    f = Fernet(fernet_key)
    encrypted_data = f.encrypt(data.encode()).decode()
    return encrypted_data


def decrypt_json_data(data):
    data = decrypt_data(data)
    return json.loads(data)


def encrypt_json_data(data):
    data = json.dumps(data)
    return encrypt_data(data)

