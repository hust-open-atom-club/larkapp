from larkapp.base import BaseLarkBot


class LarkEmailBot(BaseLarkBot):
    secret: str
    url: str

    def __init__(self) -> None:
        super().__init__()
