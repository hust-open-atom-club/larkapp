import dotenv

from larkapp import hr

dotenv.load_dotenv(dotenv_path=".env")

hr.test_members()
