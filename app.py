# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import string, random
from urllib.parse import urlparse

DB = "urls.db"
CODE_LENGTH = 6

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-random-secret"  # change for production

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

def generate_code(length=CODE_LENGTH):
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

def save_url(code, long_url):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO urls (code, long_url) VALUES (?, ?)", (code, long_url))
    conn.commit()
    conn.close()

def get_long_url(code):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT long_url, visits FROM urls WHERE code = ?", (code,))
    row = cur.fetchone()
    conn.close()
    return row  # (long_url, visits) or None

def increment_visits(code):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE urls SET visits = visits + 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and parsed.netloc != ""
    except:
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        long_url = request.form.get("url", "").strip()
        custom = request.form.get("custom_code", "").strip()
        if not long_url:
            flash("Please enter a URL.")
            return redirect(url_for("index"))
        if not is_valid_url(long_url):
            flash("Please enter a valid URL starting with http:// or https://")
            return redirect(url_for("index"))

        if custom:
            # optionally allow custom codes
            if code_exists(custom):
                flash("Custom code already taken — try another.")
                return redirect(url_for("index"))
            code = custom
        else:
            code = generate_code()

        save_url(code, long_url)
        short_url = request.url_root.rstrip("/") + "/" + code
        return render_template("result.html", short_url=short_url, code=code)
    return render_template("index.html")

@app.route("/<code>")
def go(code):
    row = get_long_url(code)
    if row:
        long_url, _ = row
        increment_visits(code)
        return redirect(long_url)
    return render_template("404.html"), 404

@app.route("/stats/<code>")
def stats(code):
    row = get_long_url(code)
    if row:
        long_url, visits = row
        short_url = request.url_root.rstrip("/") + "/" + code
        return render_template("result.html", short_url=short_url, code=code, long_url=long_url, visits=visits)
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
