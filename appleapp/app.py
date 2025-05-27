from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'

VOUCHER_FILE = 'vouchers.csv'
ADMIN_PASSWORD = 'admin123'

def load_vouchers():
    if os.path.exists(VOUCHER_FILE):
        return pd.read_csv(VOUCHER_FILE)
    else:
        return pd.DataFrame(columns=["code", "start_date", "type"])

def save_vouchers(df):
    df.to_csv(VOUCHER_FILE, index=False)

@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        code = request.form["code"].strip()
        df = load_vouchers()
        match = df[df["code"] == code]

        if not match.empty:
            start_date = datetime.strptime(match.iloc[0]["start_date"], "%Y-%m-%d")
            days = int(match.iloc[0]["type"].replace(" days", ""))
            end_date = start_date + timedelta(days=days)
            remaining = (end_date - datetime.now()).days

            if remaining >= 0:
                message = f"VALID - Expires on {end_date.strftime('%Y-%m-%d')} ({remaining} days left)"
                return render_template("index.html", message=message, status="valid")
            else:
                message = "EXPIRED"
        else:
            message = "INVALID CODE"
    return render_template("index.html", message=message)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("logged_in"):
        return redirect("/login")

    df = load_vouchers()
    total = len(df)
    expired = 0
    active = 0
    today = datetime.now()

    for _, row in df.iterrows():
        start_date = datetime.strptime(row["start_date"], "%Y-%m-%d")
        days = int(row["type"].replace(" days", ""))
        end_date = start_date + timedelta(days=days)
        if end_date < today:
            expired += 1
        else:
            active += 1

    if request.method == "POST":
        code = request.form["code"].strip()
        start_date = request.form["start_date"]
        vtype = request.form["type"]
        df = df.append({"code": code, "start_date": start_date, "type": vtype}, ignore_index=True)
        save_vouchers(df)
        return redirect("/admin")

    return render_template("admin.html", total=total, active=active, expired=expired)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/admin")
        else:
            error = "Invalid Password"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)