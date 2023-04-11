from larkapp import LarkApp


def test_get_metainfo():
    app = LarkApp(
        app_id="cli_a4beae5db8f8500e", app_secret="MYJt7hkEpMSXxwlK5Kvs3cy7jch5iye7"
    )

    # app.get_metainfo()
    app.check_new_info()


if __name__ == "__main__":
    test_get_metainfo()
