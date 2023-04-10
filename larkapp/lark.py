# from larkapp.web import app

import typer
import schedule

import requests

from larkapp.util import get_token


class LarkApp:
    def __init__(self, app_id: str, app_secret: str) -> None:
        if app_id is None or app_secret is None:
            raise Exception("app_id or app_secret is None")

        self.token = get_token(app_id, app_secret)

        self.spreadsheetToken = "shtcnEEqrGPV0GQUAI4Zfalpqad"
        self.app_token = "SGDMbFZuyasuOAsLCi7cRZ83nfe"

        # 接下来的值可以自动获取
        self.sheet_id = "37f4ec"
        self.table_id = "tblPHPdEzAkq21OG"
        self.view_id = "vewz9hUZSJ"

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

        typer.echo(self.sheet_id)

        # --------------------------------------------#
        # 获取多维表格的数据表
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
            if item.get("name") == "Linux Kernel":
                self.table_id = item.get("table_id")
                break

        # TODO: 有更简单的写法吗？

        if self.table_id is None:
            raise Exception("Failed to get table_id")

        typer.echo(self.table_id)

        #--------------------------------------------#
        # 获取视图的view_id
        #--------------------------------------------#

        views_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/views"
        params = {}

        response = requests.request("GET", views_url, headers=headers, params=params)
        if response.json().get("code") != 0:
            raise Exception("Failed to get bitable views")
        
        content = response.json().get("data").get("items")

        # 根据view_name查找所需的view_id
        self.view_id = None
        for item in content:
            if item.get("view_name") == "Kernel":
                self.view_id = item.get("view_id")
                break

        if self.view_id is None:
            raise Exception("Failed to get view_id")
        
        typer.echo(self.view_id)

        pass

    def run(self) -> None:
        schedule.every(30).minutes.do(self.check_mail)

        pass

    def check_mail(self) -> None:
        # TODO: 用于自动 check 邮件列表内的更新
        #       需要读取邮箱并对应至用户名，然后用机器人发送消息@之
        #       获取邮件列表的方法在寝室内的机器上
        #       需要使用另一个群组bot

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

        pass
