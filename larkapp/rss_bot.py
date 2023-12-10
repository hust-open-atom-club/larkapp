import os
import re
import time
from datetime import datetime

import feedparser
import requests
import schedule
from rich import print

from larkapp.base import BaseLarkBot
from larkapp.hr import get_all_members, get_kernel_members
from larkapp.util import escape_markdown, get_token


class LarkRSSBot(BaseLarkBot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def run(self) -> None:
        print("[green]BOT[/green] start running RSS bot @ {}".format(datetime.now()))

        try:
            feed = feedparser.parse("https://lore.kernel.org/lkml/?q=hust.edu.cn&x=A")

        except Exception as e:
            print("[red]ERROR[/red] failed to fetch RSS feed: {}".format(e))
            return

        app_id = os.getenv("APP_ID")
        app_secret = os.getenv("APP_SECRET")

        try:
            token = get_token(app_id, app_secret)  # type: ignore

        except Exception as e:
            print("[red]ERROR[/red] failed to get access token: {}".format(e))
            return

        elements = []

        new_count = 0
        reply_count = 0

        entries = []

        for entry in feed.entries:
            updated = entry.updated

            if updated > self.last_updated:
                entries.append(entry)
            else:
                break

        if len(entries) == 0:
            print("[green]BOT[/green] no new entries")
            print(
                "[green]BOT[/green]   end running RSS bot @ {}".format(datetime.now())
            )
            return

        # 这里将由文件获取all_members换为使用飞书API获取
        all_members = get_all_members(token)
        kernel_members = get_kernel_members(token)

        for entry in entries:
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
                            "content": f"<at id={id}></at> {email}\n[{escape_markdown(entry.title)}]({escape_markdown(entry.link)})",
                        }
                    )
                    continue

            print("[red]ALERT[/red] cannot find name for {}".format(email))
            elements.append(
                {
                    "tag": "markdown",
                    "content": f"{entry.author}\n[{escape_markdown(entry.title)}]({escape_markdown(entry.link)})",
                }
            )

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

                print(
                    "[green]BOT[/green]   end running RSS bot @ {}".format(
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
            print(
                "[green]BOT[/green]   end running RSS bot @ {}".format(datetime.now())
            )
            return

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
    WEBHOOK_SECRET = os.getenv("TEST_WEBHOOK_SECRET", default=None)
    WEBHOOK_URL = os.getenv("TEST_WEBHOOK_URL", default=None)

    bot = LarkBot(secret=WEBHOOK_SECRET, url=WEBHOOK_URL)  # type: ignore

    bot.last_updated = "2023-05-23T16:08:25Z"

    schedule.every(10).minutes.do(bot.run)

    schedule.run_all()

    while True:
        schedule.run_pending()
        time.sleep(1)
