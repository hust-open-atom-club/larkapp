import json
import requests

from rich import print


def get_token(app_id: str, app_secret: str) -> str:
    # print(f"[blue]APP[/blue] app_id: {app_id} app_secret: {app_secret}")

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps(
        {
            "app_id": app_id,
            "app_secret": app_secret,
        }
    )

    headers = {"Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)

    tenant_access_token = response.json().get("tenant_access_token")

    if tenant_access_token is None:
        raise Exception("Failed to get tenant_access_token")

    # print("[blue]APP[/blue] tenant_access_token: {0}".format(tenant_access_token))

    return tenant_access_token


def escape_markdown(text: str):
    """
    return text escaped given entity types
    :param text: text to escape
    :param entity_type: entities to escape
    :return:
    """
    # de-escape and escape again to avoid double escaping
    return text.replace('\\*', '*').replace('\\`', '`').replace('\\_', '_')\
        .replace('\\~', '~').replace('\\>', '>').replace('\\[', '[')\
        .replace('\\]', ']').replace('\\(', '(').replace('\\)', ')')\
        .replace('*', '\\*').replace('`', '\\`').replace('_', '\\_')\
        .replace('~', '\\~').replace('>', '\\>').replace('[', '\\[')\
        .replace(']', '\\]').replace('(', '\\(').replace(')', '\\)')
