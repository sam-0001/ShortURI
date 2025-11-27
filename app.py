from flask import Flask, request, redirect, send_from_directory
import sqlite3
import string, random
from urllib.parse import urlparse
import os

app = Flask(__name__)
DB = "urls.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        long_url TEXT,
        visits INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not code_exists(code):
            return code


def code_exists(code):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM urls WHERE code = ?", (code,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def save_url(code, url):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO urls (code, long_url) VALUES (?, ?)", (code, url))
    conn.commit()
    conn.close()


def get_url(code):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT long_url, visits FROM urls WHERE code=?", (code,))
    row = cur.fetchone()
    conn.close()
    return row


def increment(code):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE urls SET visits = visits + 1 WHERE code=?", (code,))
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/style.css")
def css():
    return send_from_directory(".", "style.css")


@app.route("/shorten", methods=["POST"])
def shorten():
    long_url = request.form.get("url")

    if not long_url:
        return "Enter URL"

    code = generate_code()
    save_url(code, long_url)

    short_url = request.url_root.rstrip("/") + "/" + code

    # manually fill data in result.html
    with open("result.html") as f:
        html = f.read()
        html = html.replace("{{short}}", short_url)
        html = html.replace("{{code}}", code)
    return html


@app.route("/<code>")
def go(code):
    row = get_url(code)
    if not row:
        return send_from_directory(".", "notfound.html")

    long_url, _ = row
    increment(code)
    return redirect(long_url)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
