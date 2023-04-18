from flask import Flask, request

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def hello_world():
    print(request.json)

    return "Hello, World!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=22000, debug=True)
