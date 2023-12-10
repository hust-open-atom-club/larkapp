from larkapp.base import BaseLarkBot


class LarkEmailBot(BaseLarkBot):
    secret: str
    url: str

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
