import base64
import hashlib
import hmac
from datetime import datetime


class BaseLarkBot:
    secret: str
    url: str

    def __init__(self, secret: str, url: str) -> None:
        if (not secret) or (not url):
            raise ValueError("invalid init arguments")

        self.secret = secret
        self.url = url
        self.last_updated = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def gen_sign(self, timestamp: int) -> str:
        string_to_sign = "{}\n{}".format(timestamp, self.secret)
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode("utf-8")

        return sign
