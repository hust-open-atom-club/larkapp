# from larkapp.web import app
import datetime
import json
import os

import requests
from rich import print

from larkapp.rss_bot import LarkRSSBot
from larkapp.util import get_token


class LarkApp:
    def __init__(self, app_id: str, app_secret: str) -> None:
        if app_id is None or app_secret is None:
            raise Exception("app_id or app_secret is None")

        self.app_id = app_id
        self.app_secret = app_secret

        self.token = get_token(self.app_id, self.app_secret)

        self.spreadsheetToken = os.getenv(
            "KERNEL_SPREADSHEETTOKEN", default=None
        )  # Kernel 成员信息表id
        self.app_token = os.getenv("KERNEL_APP_TOKEN", default=None)  # Kernel 多维表格id

        WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", default=None)
        WEBHOOK_URL = os.getenv("WEBHOOK_URL", default=None)

        self.bot = LarkBot(secret=WEBHOOK_SECRET, url=WEBHOOK_URL)  # type: ignore

        pass

    def get_sheet_id(self, spreadsheetToken: str) -> str:
        # --------------------------------------------#
        # 获取表格元数据以获取sheetid
        # --------------------------------------------#

        metainfo_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheetToken}/metainfo"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        response = requests.request("GET", metainfo_url, headers=headers)
        if response.json().get("code") != 0:
            print("[red]ALERT[/red] Failed to get spreadsheet metainfo")
            return ""
            # raise Exception("Failed to get spreadsheet metainfo")

        sheet_id = response.json().get("data").get("sheets")[0].get("sheetId")

        print("[blue]APP[/blue] sheet_id: {0}".format(sheet_id))

        return sheet_id

    def get_table_id_by_name(self, name: str) -> str:
        # --------------------------------------------#
        # 获取多维表格的数据表table_id
        # --------------------------------------------#

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        tables_url = (
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables"
        )
        params = {}

        response = requests.request("GET", tables_url, headers=headers, params=params)
        if response.json().get("code") != 0:
            print("[red]ALERT[/red] Failed to get bitable tables")
            return ""
            # raise Exception("Failed to get bitable tables")

        content = response.json().get("data").get("items")

        table_id = None
        for item in content:
            # TODO: 注意这里是按照名称来获取的，如果名称不一致，会导致获取失败
            if item.get("name") == name:
                table_id = item.get("table_id")
                break

        # TODO: 有更简单的写法吗？

        if table_id is None:
            print("[red]ALERT[/red] Failed to get table_id")
            return ""
            # raise Exception("Failed to get table_id")

        # print("[blue]APP[/blue] table_id: {}".format(table_id))

        return table_id

    def run(self) -> None:
        # 再次获取token，避免token过期
        self.token = get_token(self.app_id, self.app_secret)
        self.check_new_info()

        pass

    def check_new_info(self) -> None:
        # 检查包含成员信息的文档是否有新增成员，如果有，则检查是否分配了PATCH，如果没有，则先在新手任务中分配一个？
        # 这里的逻辑得问一下亮哥，可以先按照分配PATCH来写。

        # 需要的权限：读取表格，写入多维表格

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        from larkapp.hr import get_kernel_members

        members = [member.name for member in get_kernel_members(self.token)]

        # TODO: 自动分配 Copilot

        # ---------------------------------------------#
        # 获取所有的记录，仅保留所有Assignees并去重？
        # 也使用按条件过滤的API
        # ---------------------------------------------#

        table_id = self.get_table_id_by_name("Linux Kernel")

        records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
        params = {"filter": 'AND(CurrentValue.[Assignees]!="")'}

        response = requests.request("GET", records_url, headers=headers, params=params)
        if response.json().get("code") != 0:
            print("[red]ALERT[/red] Failed to get bitable records")
            return
            # raise Exception("Failed to get bitable records")

        record_list = response.json().get("data").get("items")
        if record_list is None or len(record_list) == 0:
            print("[purple]INFO[/purple] failed to get assignees")
            return

        assignees_list = [
            item.get("fields").get("Assignees")[0].get("name") for item in record_list
        ]

        # ---------------------------------------------#
        # 利用筛选条件检索没有分配者且为 True Positive 且 Comments 为空的记录
        # ---------------------------------------------#

        records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
        params = {
            "filter": 'AND(CurrentValue.[Assignees]="",CurrentValue.[Type]="True Positive",CurrentValue.[Comments]="")'
        }

        response = requests.request("GET", records_url, headers=headers, params=params)
        if response.json().get("code") != 0:
            print("[red]ALERT[/red] Failed to get bitable records")
            return
            # raise Exception("Failed to get bitable records")

        record_list = response.json().get("data").get("items")
        if record_list is None or len(record_list) == 0:
            print("[purple]INFO[/purple] No record needs to assign")
            return

        # ---------------------------------------------#
        # 遍历记录，分配PATCH
        # TODO: 逻辑需要调整
        # ---------------------------------------------#

        # 获取差集
        members_set = set(members)
        assignees_set = set(assignees_list)

        diff_set = members_set.difference(assignees_set)
        if diff_set is None or len(list(diff_set)) == 0:
            print("[purple]INFO[/purple] No member needs to assign")
            return

        diff_list = list(diff_set)
        print(f"[blue]APP[/blue] diff_list: {diff_list}")

        # 分配PATCH
        # 首先获取全部用户的信息，包括姓名与open_id
        from larkapp.hr import get_all_members

        all_members = get_all_members(self.token)

        # 白名单
        # white_list = []
        white_list = [
            "罗昊",
            "周文宇",
            "陈骏",
            "邵正昊",
            "黄莉雯",
            "黄畅怡",
            "李佩芝",
            "易迎澳",
            "江帅",
            "娄峥",
            "王俊海",
        ]

        elements = []

        for diff in diff_list:
            # 检查是否在白名单中
            if diff in white_list:
                continue

            # 检查是否还有可分配的PATCH
            if record_list is None or len(record_list) == 0:
                print("[purple]INFO[/purple] No record needs to assign")
                return

            assignees = None

            for member in all_members:
                if member.name == diff:
                    assignees = member.dict()
                    break

            if assignees is None:
                print("[red]ALERT[/red] Failed to get assignees of {}".format(diff))
                continue

            # TODO: 这里需要通过name来查找对应的en_name，email和用户id！！！！
            #       最终解决方案：通过获取填写了信息储备表的用户的信息，然后通过name来查找对应的信息

            print(assignees)

            # 从上到下分配PATCH
            record = record_list.pop(0)

            # 更新记录
            record_id = record.get("record_id")

            update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}"
            fields = record.get("fields")

            bug_info = fields.get("Bug Information")

            assignees_id = assignees.get("id")

            elements.append(
                {
                    "tag": "markdown",
                    "content": f"{bug_info} assigned to <at id={assignees_id}></at>",
                }
            )

            continue

            fields.update(
                {
                    "Assignees": assignees,
                    "Patch Progress": 0.1,
                    "Task Date": int(datetime.datetime.now().timestamp()) * 1000,
                    "Patch Copilot": [
                        {
                            "email": "",
                            "en_name": os.getenv("COPILOT_NAME", default=None),
                            "id": os.getenv("COPILOT_ID", default=None),
                            "name": os.getenv("COPILOT_NAME", default=None),
                        }
                    ],
                }
            )

            data = json.dumps({"fields": fields})

            print("[blue]APP[/blue] new assign", fields.get("Bug Information"))

            response = requests.request("PUT", update_url, headers=headers, data=data)
            if response.json().get("code") != 0:
                print("[red]ALERT[/red] Failed to update bitable records")
                return
                # raise Exception("Failed to update bitable records")

        # 发送消息
        if len(elements) != 0:
            print(elements)
            # self.bot.send_msg(elements)

        pass

    def update_status(self) -> None:
        pass
