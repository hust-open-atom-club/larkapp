# from larkapp.web import app
import json
import random

import typer

import requests

from larkapp.util import get_token


class LarkApp:
    def __init__(self, app_id: str, app_secret: str) -> None:
        if app_id is None or app_secret is None:
            raise Exception("app_id or app_secret is None")

        self.token = get_token(app_id, app_secret)

        self.spreadsheetToken = "shtcnIOEYcbbwoVQQZsKBgiuNFe"
        self.app_token = "SGDMbFZuyasuOAsLCi7cRZ83nfe"

        # 接下来的值可以自动获取

        self.get_metainfo()

        self.sheet_id = "Ht5RNk"
        self.table_id = "tblPHPdEzAkq21OG"

        pass

    def get_metainfo(self) -> None:
        # 自动化获取sheet_id, table_id, view_id
        # 非必需，也可以每次初始化都运行来避免填写的数据太多

        # --------------------------------------------#
        # 获取表格元数据以获取sheetid
        # --------------------------------------------#

        metainfo_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheetToken}/metainfo"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        response = requests.request("GET", metainfo_url, headers=headers)
        if response.json().get("code") != 0:
            raise Exception("Failed to get spreadsheet metainfo")

        self.sheet_id = response.json().get("data").get("sheets")[0].get("sheetId")

        typer.echo("sheet_id: {0}".format(self.sheet_id))

        # --------------------------------------------#
        # 获取多维表格的数据表table_id
        # --------------------------------------------#

        tables_url = (
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables"
        )
        params = {}

        response = requests.request("GET", tables_url, headers=headers, params=params)
        if response.json().get("code") != 0:
            raise Exception("Failed to get bitable tables")

        content = response.json().get("data").get("items")

        self.table_id = None
        for item in content:
            # TODO: 注意这里是按照名称来获取的，如果名称不一致，会导致获取失败
            if item.get("name") == "Linux Kernel":
                self.table_id = item.get("table_id")
                break

        # TODO: 有更简单的写法吗？

        if self.table_id is None:
            raise Exception("Failed to get table_id")

        typer.echo("table_id: {}".format(self.table_id))

        pass

    def run(self) -> None:

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

        # --------------------------------------------#
        # 然后获取表格内容
        # --------------------------------------------#

        content_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheetToken}/values_batch_get"
        params = {"ranges": f"{self.sheet_id}"}

        response = requests.request("GET", content_url, headers=headers, params=params)
        if response.json().get("code") != 0:
            raise Exception("Failed to get spreadsheet content")

        # 将表格内容解析为dict，其中第一列的值为key，其他列的值为value（列表）
        # 注意第一行不需要，因为是表头
        content = response.json().get("data").get("valueRanges")[0].get("values")[1:]
        if len(content) == 0:
            raise Exception("Failed to get spreadsheet content")

        members = [item[0] for item in content]
        # typer.echo(members)

        # TODO: 自动分配 Copilot

        # 需要找亮哥对一下自动分配 PATCH 的逻辑

        # ---------------------------------------------#
        # 获取所有的记录，仅保留所有Assignees并去重？
        # 也使用按条件过滤的API
        # ---------------------------------------------#

        records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        params = {"filter": 'AND(CurrentValue.[Assignees]!="")'}

        response = requests.request("GET", records_url, headers=headers, params=params)
        if response.json().get("code") != 0:
            raise Exception("Failed to get bitable records")

        record_list = response.json().get("data").get("items")
        if len(record_list) == 0:
            typer.echo("Record Error")
            return

        assignees_list = [item.get("fields").get("Assignees") for item in record_list]

        # ---------------------------------------------#
        # 利用筛选条件检索没有分配者且为 True Positive 且 Comments 为空的记录
        # ---------------------------------------------#

        records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        params = {
            "filter": 'AND(CurrentValue.[Assignees]="",CurrentValue.[Type]="True Positive",CurrentValue.[Comments]="")'
        }

        response = requests.request("GET", records_url, headers=headers, params=params)
        if response.json().get("code") != 0:
            raise Exception("Failed to get bitable records")

        record_list = response.json().get("data").get("items")
        if len(record_list) == 0:
            typer.echo("No record needs to assign")
            return

        # ---------------------------------------------#
        # 遍历记录，分配PATCH
        # TODO: 逻辑需要调整
        # ---------------------------------------------#

        # 获取差集
        members_set = set(members)
        assignees_set = set(assignees_list)

        diff_set = members_set.difference(assignees_set)
        diff_list = list(diff_set)

        typer.echo(diff_list)

        # 分配PATCH

        for diff in diff_list:
            # 检查是否还有可分配的PATCH
            if record_list is None or len(record_list) == 0:
                typer.echo("No record needs to assign")
                return

            # 随机分配一个PATCH
            record = random.choice(record_list)
            typer.echo(record)

            # 更新记录
            record_id = record.get("record_id")

            update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
            fields = record.get("fields")
            fields.update({"Assignees": str(diff), "Patch Progress": 0.1})

            typer.echo(fields)

            data = json.dumps({"fields": fields})

            typer.echo(fields.get("Bug Information"))

            response = requests.request("PUT", update_url, headers=headers, data=data)
            if response.json().get("code") != 0:
                typer.echo(response.json())
                raise Exception("Failed to update bitable records")
            
            # 从记录列表中删除已分配的记录
            record_list.remove(record)

            
        pass


    def update_status(self) -> None:
        pass