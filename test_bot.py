import dotenv

from larkapp.rss_bot import test_bot

dotenv.load_dotenv(dotenv_path=".env")

test_bot()
