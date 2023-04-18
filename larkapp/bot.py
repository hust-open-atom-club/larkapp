import base64
import hashlib
import hmac
import os
import re
import time
from datetime import datetime

from rich import print
import feedparser
import requests
import schedule

from larkapp.hr import get_all_members, get_kernel_members
from larkapp.util import get_token


class LarkBot:
    def __init__(self, secret: str, url: str) -> None:
        if (not secret) or (not url):
            raise ValueError("invalid init arguments")

        self.secret = secret
        self.url = url
        self.last_updated = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        # self.last_updated = "2023-04-18T09:25:58Z"

    def gen_sign(self, timestamp: int) -> str:
        string_to_sign = "{}\n{}".format(timestamp, self.secret)
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode("utf-8")

        return sign

    def run(self) -> None:
        print("[green]BOT[/green] start running RSS bot @ {}".format(datetime.now()))

        try:
            feed = feedparser.parse("https://lore.kernel.org/lkml/?q=hust.edu.cn&x=A")

        except Exception as e:
            print("[red]ERROR[/red] failed to fetch RSS feed: {}".format(e))
            return

        app_id = os.getenv("APP_ID")
        app_secret = os.getenv("APP_SECRET")
        token = get_token(app_id, app_secret)  # type: ignore

        all_members = get_all_members(token)
        kernel_members = get_kernel_members(token)

        elements = []

        new_count = 0
        reply_count = 0

        for entry in feed.entries:
            updated = entry.updated

            if updated > self.last_updated:
                print("[green]BOT[/green] new entry: {}".format(entry.title))

                if entry.title.startswith("Re:"):
                    reply_count += 1
                else:
                    new_count += 1

                email = re.search(r"\((.*?)\)", entry.author).group(1)  # type: ignore

                # 在kernel_members中按照email查找人名
                name_list = list(filter(lambda x: x.email == email, kernel_members))
                if name_list is not None and len(name_list) != 0:
                    name = name_list[0].name

                    # 若能搜索到人名，则在all_members中按照人名查找id
                    id_list = list(filter(lambda x: x.name == name, all_members))
                    if id_list is not None and len(id_list) != 0:
                        id = id_list[0].id
                        elements.append(
                            {
                                "tag": "markdown",
                                "content": f"<at id={id}></at> {email}\n[{entry.title}]({entry.link})",
                            }
                        )
                        continue

                print("[red]ALERT[/red] cannot find name for {}".format(email))
                elements.append(
                    {
                        "tag": "markdown",
                        "content": f"{entry.author}\n[{entry.title}]({entry.link})",
                    }
                )
            else:
                break

        if len(elements) == 0:
            print("[green]BOT[/green] no new entries")
            return

        timestamp = int(datetime.now().timestamp())
        sign = self.gen_sign(timestamp)

        params = {
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "interactive",
            "card": {
                "elements": elements,
                "header": {
                    "template": "blue",
                    "title": {
                        "content": f"LKML: {new_count} new, {reply_count} reply",
                        "tag": "plain_text",
                    },  # TODO
                },
            },
        }

        try:
            resp = requests.post(url=self.url, json=params)
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") and result["code"] != 0:
                print("[red]ERROR[/red] {}".format(result["msg"]))
                print(
                    "[red]ERROR[/red] failed to send message @ {}".format(
                        datetime.now()
                    )
                )
                return

            self.last_updated = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            print(
                "[green]BOT[/green] successfully sent message @ {}".format(
                    datetime.now()
                )
            )

        except Exception as e:
            print("[red]ERROR[/red] failed to send message: {}".format(e))

    def send_msg(self, elements) -> None:
        print("[green]BOT[/green] send msg @ {}".format(datetime.now()))

        timestamp = int(datetime.now().timestamp())
        sign = self.gen_sign(timestamp)

        params = {
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "interactive",
            "card": {
                "elements": elements,
                "header": {
                    "template": "blue",
                    "title": {
                        "content": "New PATCH Assigned",
                        "tag": "plain_text",
                    },
                },
            },
        }

        try:
            resp = requests.post(url=self.url, json=params)
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") and result["code"] != 0:
                print("[red]ERROR[/red] {}".format(result["msg"]))
                print(
                    "[red]ERROR[/red] failed to send message @ {}".format(
                        datetime.now()
                    )
                )
                return

            print(
                "[green]BOT[/green] successfully sent message @ {}".format(
                    datetime.now()
                )
            )

        except Exception as e:
            print("[red]ERROR[/red] failed to send message: {}".format(e))


def test_bot():
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", default=None)
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", default=None)

    bot = LarkBot(secret=WEBHOOK_SECRET, url=WEBHOOK_URL)  # type: ignore

    schedule.every(10).minutes.do(bot.run)

    schedule.run_all()

    while True:
        schedule.run_pending()
        time.sleep(1)
