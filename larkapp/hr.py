import os

from rich import print
import requests

from larkapp.util import get_token
from larkapp.model import LarkUser


def get_all_members(token: str) -> list[LarkUser]:
    # 获取信息储备表中的所有成员信息
    # 成员信息格式
    # {'email': '', 'en_name': '人人人', 'id': 'ou_98ec34393837435008f0642dabe62b35', 'name': '人人人'}

    app_token = os.getenv("INFO_APP_TOKEN", default=None)  # 信息储备表的app_token

    table_id = os.getenv("INFO_TABLE_ID", default=None)  # 信息储备表的table_id

    headers = {"Authorization": f"Bearer {token}"}

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    params = {"filter": 'CurrentValue.[姓名]!=""'}

    response = requests.get(url=url, headers=headers, params=params)
    if response.json().get("code") != 0:
        print("[red]ALERT[/red] Failed to get all members from sheet")
        return []
        # raise Exception("Failed to get all members from sheet")

    members: list[LarkUser] = []

    items = response.json().get("data").get("items")

    for item in items:
        fields = item.get("fields")

        if fields.get("飞书账号") is None:
            continue

        user = fields.get("飞书账号")[0]

        email = user.get("email")
        en_name = user.get("en_name")
        name = user.get("name")
        id = user.get("id")

        new_member = LarkUser(email, en_name, name, id)

        members.append(new_member)

    return members


def get_kernel_members(token: str) -> list[LarkUser]:
    spreadsheetToken = os.getenv(
        "KERNEL_SPREADSHEETTOKEN", default=None
    )  # kernel群信息表的spreadsheetToken
    sheet_id = os.getenv("KERNEL_SHEET_ID", default=None)  # kernel群信息表的sheet_id

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    content_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheetToken}/values_batch_get"
    params = {"ranges": sheet_id}

    response = requests.request("GET", content_url, headers=headers, params=params)

    # print(response.json())

    if response.json().get("code") != 0:
        print("[red]ALERT[/red] Failed to get spreadsheet content")
        return []
        # raise Exception("Failed to get spreadsheet content")

    members: list[LarkUser] = []

    # 注意第一行的表头，不需要解析
    content = response.json().get("data").get("valueRanges")[0].get("values")[1:]
    if content is None or len(content) == 0:
        print("[red]ALERT[/red] Failed to get spreadsheet content")
        return []

    members = []

    for item in content:
        name = item[0]
        en_name = item[0]

        if item[2] is None:
            print(f"[red]ALERT[/red] Failed to get email of {name}")
            continue

        email = item[2][0].get("text", None)
        if email is None or email == "":
            email = item[2][1].get("text", None)
        id = ""

        new_member = LarkUser(email, en_name, name, id)

        members.append(new_member)

    return members


def get_iot_members(token: str) -> list[LarkUser]:
    return []


def test_members():
    token = get_token(
        app_id=os.getenv("APP_ID", default=None),  # type: ignore
        app_secret=os.getenv("APP_SECRET", default=None),  # type: ignore
    )
    members = get_all_members(token)
    print([str(item) for item in members])

    members = get_kernel_members(token)
    print([(member.name, member.email) for member in members])
