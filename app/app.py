import os

from flask import Flask, request, jsonify

app = Flask(__name__)
app.json.ensure_ascii = False


@app.get("/")
def hello():
    return jsonify({
        "message": os.getenv("APP_MESSAGE", "Биба и Боба"),
        "author": os.getenv("APP_AUTHOR", "Укажи своё имя"),
        "tokenConfigured": bool(os.getenv("APP_TOKEN"))
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
