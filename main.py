import os
import time

import typer
import schedule

from larkapp import LarkApp
from larkapp import LarkBot

cli = typer.Typer()


@cli.command()
def run(app_id: str, app_secret: str):
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", default="RQPuPNQm0ZxjT5SzDlArPf")
    WEBHOOK_URL = os.getenv(
        "WEBHOOK_URL",
        default="https://open.feishu.cn/open-apis/bot/v2/hook/7daa6d5c-ceb9-4027-9551-9ea64db3905c",
    )

    bot = LarkBot(secret=WEBHOOK_SECRET, url=WEBHOOK_URL)

    app = LarkApp(app_id, app_secret)

    schedule.every(10).minutes.do(bot.run)
    schedule.every(2).minutes.do(app.run)

    schedule.run_all()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    cli()


# app = LarkApp(app_id="cli_a4beae5db8f8500e", app_secret="MYJt7hkEpMSXxwlK5Kvs3cy7jch5iye7")

