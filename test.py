import dotenv
import os

from larkapp import LarkApp


def test():
    app = LarkApp(
        app_id=os.getenv("APP_ID", default=None),  # type: ignore
        app_secret=os.getenv("APP_SECRET", default=None),  # type: ignore
    )

    # app.get_metainfo()
    app.check_new_info()


if __name__ == "__main__":
    dotenv.load_dotenv(dotenv_path=".env")

    test()
