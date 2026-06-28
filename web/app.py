# FILE: web/app.py

from flask import Flask, render_template, jsonify, request
from core.config import WEB_HOST, WEB_PORT, ADMIN_ID

app = Flask(__name__)


# ---------- DASHBOARD ----------
@app.route("/")
def dashboard():
    return """
    <html>
        <head>
            <title>ZarVPN Panel</title>
            <style>
                body { font-family: Arial; background:#0f172a; color:white; text-align:center; }
                .box { margin-top:100px; }
                .card { background:#1e293b; padding:20px; border-radius:10px; display:inline-block; }
            </style>
        </head>

        <body>
            <div class="box">
                <div class="card">
                    <h2>🔥 ZarVPN Web Panel</h2>
                    <p>Status: Running ✅</p>
                </div>
            </div>
        </body>
    </html>
    """


# ---------- API STATUS ----------
@app.route("/api/status")
def status():
    return jsonify({
        "status": "ok",
        "service": "zarvpn",
        "admin": ADMIN_ID
    })


# ---------- USERS API ----------
@app.route("/api/users")
def users():
    return jsonify({
        "message": "users api ready (next step database connect)"
    })


def start_web():
    print("WEB PANEL STARTED ✅")
    app.run(host=WEB_HOST, port=WEB_PORT)
