from flask import Flask, render_template, request, redirect, url_for, session
import numpy as np
import joblib
import os
import sqlite3

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from database import init_db
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

from io import BytesIO
from flask import send_file
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
init_db()

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

# Load trained model and scaler
model = joblib.load("bank_churn_model.pkl")
scaler = joblib.load("scaler.pkl")

@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/login/callback")
def authorize():
    token = google.authorize_access_token()

    user = token["userinfo"]

    session["user"] = {
        "name": user["name"],
        "email": user["email"],
        "picture": user["picture"]
    }

    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/")
def home():

    if "user" not in session:
        return render_template("login.html")

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    email = session["user"]["email"]

    cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_email=?",
        (email,)
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_email=? AND risk_level='High'",
        (email,)
    )
    high = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_email=? AND risk_level='Medium'",
        (email,)
    )
    medium = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_email=? AND risk_level='Low'",
        (email,)
    )
    low = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        user=session["user"],
        total=total,
        high=high,
        medium=medium,
        low=low
    )

@app.route("/prediction")
def prediction():

    if "user" not in session:
        return redirect(url_for("home"))

    return render_template(
        "index.html",
        user=session["user"]
    )

@app.route("/download-report")
def download_report():

    if "user" not in session:
        return redirect(url_for("home"))

    if "last_prediction" not in session:
        return redirect(url_for("prediction"))

    data = session["last_prediction"]

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    title = styles["Heading1"]
    title.alignment = TA_CENTER

    elements = []

    elements.append(Paragraph("Bank Customer Churn Prediction Report", title))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    table_data = [

        ["Customer", session["user"]["name"]],

        ["Email", session["user"]["email"]],

        ["Date", datetime.now().strftime("%d-%m-%Y %H:%M")],

        ["Probability", f'{data["probability"]}%'],

        ["Risk Level", data["risk"]],

        ["Prediction", data["prediction"]]

    ]

    table = Table(table_data, colWidths=[2.5 * inch, 4 * inch])

    table.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),

        ("GRID", (0, 0), (-1, -1), 1, colors.grey),

        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),

        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),

        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 8)

    ]))

    elements.append(table)

    elements.append(Paragraph("<br/><br/>", styles["Normal"]))

    if data["risk"] == "High":

        recommendation = """
        <b>Recommendations</b><br/>
        • Contact the customer immediately.<br/>
        • Offer special loyalty benefits.<br/>
        • Assign a relationship manager.
        """

    elif data["risk"] == "Medium":

        recommendation = """
        <b>Recommendations</b><br/>
        • Monitor customer activity.<br/>
        • Offer promotional rewards.<br/>
        • Increase customer engagement.
        """

    else:

        recommendation = """
        <b>Recommendations</b><br/>
        • Continue providing quality service.<br/>
        • Maintain customer engagement.
        """

    elements.append(Paragraph(recommendation, styles["BodyText"]))

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Prediction_Report.pdf",
        mimetype="application/pdf"
    )

@app.route("/history")
def history():

    if "user" not in session:
        return redirect(url_for("home"))

    conn = sqlite3.connect("bank.db")

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM predictions

    WHERE user_email=?

    ORDER BY id DESC

    """,(session["user"]["email"],))

    rows = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        user=session["user"],
        rows=rows
    )

@app.route("/reports")
def reports():

    if "user" not in session:
        return redirect(url_for("home"))

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    email = session["user"]["email"]

    cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_email=?",
        (email,)
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_email=? AND risk_level='High'",
        (email,)
    )
    high = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_email=? AND risk_level='Medium'",
        (email,)
    )
    medium = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_email=? AND risk_level='Low'",
        (email,)
    )
    low = cursor.fetchone()[0]

    cursor.execute("""

    SELECT *

    FROM predictions

    WHERE user_email=?

    AND risk_level='High'

    ORDER BY id DESC

    LIMIT 5

    """, (email,))

    high_rows = cursor.fetchall()

    conn.close()

    return render_template(
    "reports.html",
    user=session["user"],
    total=total,
    high=high,
    medium=medium,
    low=low,
    high_rows=high_rows
)

@app.route("/predict", methods=["POST"])
def predict():

    if "user" not in session:
        return redirect(url_for("home"))

    # Get values from the form
    credit_score = float(request.form["credit_score"])
    age = float(request.form["age"])
    tenure = float(request.form["tenure"])
    balance = float(request.form["balance"])
    num_products = float(request.form["num_products"])
    has_card = float(request.form["has_card"])
    active_member = float(request.form["active_member"])
    salary = float(request.form["salary"])

    geography = request.form["geography"]
    gender = request.form["gender"]

    # One-hot encoding
    germany = 1 if geography == "Germany" else 0
    spain = 1 if geography == "Spain" else 0

    male = 1 if gender == "Male" else 0

    features = np.array([[
        credit_score,
        age,
        tenure,
        balance,
        num_products,
        has_card,
        active_member,
        salary,
        germany,
        spain,
        male
    ]])

    features = scaler.transform(features)

    probability = model.predict_proba(features)[0][1]
    probability_percent = round(probability * 100, 2)

    if probability >= 0.70:

        prediction = "Customer is likely to churn."
        risk = "High"

    elif probability >= 0.40:

        prediction = "Customer may churn."
        risk = "Medium"

    else:

        prediction = "Customer is not likely to churn."
        risk = "Low"

# Save last prediction in session
    session["last_prediction"] = {
        "probability": probability_percent,
        "prediction": prediction,
        "risk": risk
    }

    # Save prediction to database
    conn = sqlite3.connect("bank.db")

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO predictions(
    user_name,
    user_email,
    probability,
    prediction,
    risk_level
    )
    VALUES(?,?,?,?,?)
    """, (
        session["user"]["name"],
        session["user"]["email"],
        probability_percent,
        prediction,
        risk
    ))

    conn.commit()
    conn.close()

    return render_template(
        "index.html",
        user=session["user"],
        prediction=prediction,
        probability=probability_percent
    )

if __name__ == "__main__":
    app.run(debug=True)