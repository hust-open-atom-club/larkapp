import dotenv

from larkapp.bot import test_bot

dotenv.load_dotenv(dotenv_path=".env")

test_bot()
