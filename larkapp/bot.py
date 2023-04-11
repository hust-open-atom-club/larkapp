# !/usr/bin/env python3
# coding:utf-8

# larkbot.py

import base64
import hashlib
import hmac
import os
import time
from datetime import datetime

import feedparser
import requests
import schedule


class LarkBot:
    def __init__(self, secret: str, url: str) -> None:
        if (not secret) or (not url):
            raise ValueError("invalid init arguments")

        self.secret = secret
        self.url = url
        self.last_updated = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        # self.last_updated = "2023-04-06T09:01:16Z"

    def gen_sign(self, timestamp: int) -> str:
        string_to_sign = "{}\n{}".format(timestamp, self.secret)
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode("utf-8")

        return sign

    def run(self) -> None:
        print("start running RSS bot @ {}".format(datetime.now()))

        try:
            feed = feedparser.parse("https://lore.kernel.org/lkml/?q=hust.edu.cn&x=A")

        except Exception as e:
            print("failed to fetch RSS feed: {}".format(e))
            return

        elements = []

        for entry in feed.entries:
            updated = entry.updated

            if updated > self.last_updated:
                print("new entry: {}".format(entry.title))

                elements.append(
                    {
                        "tag": "markdown",
                        "content": f"*{entry.author}*\n[{entry.title}]({entry.link})",
                    }
                )

            else:
                break

        if len(elements) == 0:
            print("no new entries")
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
                        "content": "RSS feed for PATCH",
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
                print(result["msg"])
                print("failed to send message @ {}".format(datetime.now()))
                return

            self.last_updated = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            print("successfully sent message @ {}".format(datetime.now()))

        except Exception as e:
            print("failed to send message: {}".format(e))


def test_bot():
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", default="NIW7s5jqrTVhYtFHGOsd1f")
    WEBHOOK_URL = os.getenv(
        "WEBHOOK_URL",
        default="https://open.feishu.cn/open-apis/bot/v2/hook/3b2f8e5e-35ce-416d-ba9a-62f4f1e070b4",
    )

    bot = LarkBot(secret=WEBHOOK_SECRET, url=WEBHOOK_URL)

    # bot.run()

    schedule.every(10).minutes.do(bot.run)

    while True:
        schedule.run_pending()
        time.sleep(1)

