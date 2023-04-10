import json

import typer
import requests
from larkapp import LarkApp

app = typer.Typer()


@app.command()
def run(app_id: str, app_secret: str):
    LarkApp(app_id, app_secret).run()


if __name__ == "__main__":
    app()


# app = LarkApp(app_id="cli_a4beae5db8f8500e", app_secret="MYJt7hkEpMSXxwlK5Kvs3cy7jch5iye7")
