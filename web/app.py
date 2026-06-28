# FILE: web/app.py

from flask import Flask, jsonify, request
from core.config import WEB_HOST, WEB_PORT

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <h2>ZarVPN Web Panel</h2>
    <p>Status: Running ✅</p>
    """


@app.route("/api/status")
def status():
    return jsonify({
        "status": "ok",
        "service": "zarvpn"
    })


def start_web():
    print("Web panel is running...")
    app.run(host=WEB_HOST, port=WEB_PORT)
