from flask import Flask, render_template, request, redirect, url_for, session
import numpy as np
import joblib
import os
import sqlite3

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from database import init_db
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/")
def index():

    if "user" in session:
        return redirect(url_for("dashboard"))

    return render_template("home.html")


@app.route("/signin")
def signin():

    if "user" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("signin"))

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
        return redirect(url_for("signin"))

    return render_template(
        "index.html",
        user=session["user"]
    )

@app.route("/download-report")
def download_report():

    if "user" not in session:
        return redirect(url_for("signin"))

    if "last_prediction" not in session:
        return redirect(url_for("prediction"))

    data = session["last_prediction"]

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    # Light "ledger" palette — paper background, dark-navy ink text,
    # darker gold accent for AA contrast on a light page
    PAPER = "#f7f4ec"
    PANEL = "#ffffff"
    PANEL_MUT = "#efe9db"
    INK = "#1c2333"
    INK_MUT = "#6b7280"
    GOLD = "#b8860b"
    GOLD_LINE = "#d9c290"

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontName="Times-Bold",
        fontSize=22,
        textColor=colors.HexColor(INK),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontName="Courier",
        fontSize=9,
        textColor=colors.HexColor(INK_MUT),
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontName="Times-Bold",
        textColor=colors.HexColor(GOLD),
        spaceAfter=10
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=18,
        textColor=colors.HexColor(INK)
    )

    footer_style = ParagraphStyle(
        "Footer",
        alignment=TA_CENTER,
        fontName="Courier",
        textColor=colors.HexColor(INK_MUT),
        fontSize=9
    )

    elements = []

    # =====================
    # Title
    # =====================

    elements.append(
        Paragraph(
            "BANK CUSTOMER CHURN PREDICTION REPORT",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "MACHINE LEARNING PREDICTION SUMMARY",
            subtitle_style
        )
    )

    elements.append(Spacer(1, 10))

    # =====================
    # Risk Colour
    # =====================

    if data["risk"] == "High":
        risk_color = colors.HexColor("#c0392b")
        risk_text_color = colors.white
        risk_text = "HIGH RISK"

    elif data["risk"] == "Medium":
        risk_color = colors.HexColor("#b8860b")
        risk_text_color = colors.white
        risk_text = "MEDIUM RISK"

    else:
        risk_color = colors.HexColor("#1f8f82")
        risk_text_color = colors.white
        risk_text = "LOW RISK"

    # =====================
    # Table
    # =====================

    table_data = [

        ["Customer Name", session["user"]["name"]],

        ["Email Address", session["user"]["email"]],

        ["Generated On", datetime.now().strftime("%d %B %Y  %I:%M %p")],

        ["Churn Probability", f'{data["probability"]}%'],

        ["Risk Level", risk_text],

        ["Prediction", data["prediction"]]

    ]

    table = Table(table_data, colWidths=[2.3*inch,4*inch])

    table.setStyle(TableStyle([

        ("BACKGROUND",(0,0),(0,-1),colors.HexColor(PANEL_MUT)),
        ("BACKGROUND",(1,0),(1,-1),colors.HexColor(PANEL)),

        ("TEXTCOLOR",(0,0),(0,-1),colors.HexColor(INK_MUT)),
        ("TEXTCOLOR",(1,0),(1,-1),colors.HexColor(INK)),

        ("GRID",(0,0),(-1,-1),0.75,colors.HexColor(GOLD_LINE)),

        ("FONTNAME",(0,0),(0,-1),"Courier-Bold"),
        ("FONTSIZE",(0,0),(0,-1),9),
        ("FONTNAME",(1,0),(1,-1),"Helvetica"),

        ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("TOPPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(-1,-1),12),

        ("BACKGROUND",(1,4),(1,4),risk_color),
        ("TEXTCOLOR",(1,4),(1,4),risk_text_color),
        ("FONTNAME",(1,4),(1,4),"Helvetica-Bold")

    ]))

    elements.append(table)

    elements.append(Spacer(1,20))

    # =====================
    # Interpretation
    # =====================

    elements.append(
        Paragraph(
            "Prediction Interpretation",
            heading_style
        )
    )

    if data["risk"]=="High":

        interpretation="""
This customer has a high probability of leaving the bank.

Immediate customer retention strategies are recommended.
"""

    elif data["risk"]=="Medium":

        interpretation="""
This customer has a moderate probability of churn.

Customer engagement should be monitored carefully.
"""

    else:

        interpretation="""
This customer is expected to remain loyal.

Continue providing quality banking services.
"""

    elements.append(
        Paragraph(
            interpretation,
            body_style
        )
    )

    elements.append(Spacer(1,20))

    # =====================
    # Recommendations
    # =====================

    elements.append(
        Paragraph(
            "Recommended Actions",
            heading_style
        )
    )

    if data["risk"]=="High":

        recommendation="""
✔ Contact the customer immediately.<br/>
✔ Offer personalized discounts.<br/>
✔ Assign a relationship manager.<br/>
✔ Monitor account activity closely.
"""

    elif data["risk"]=="Medium":

        recommendation="""
✔ Monitor customer activity.<br/>
✔ Offer promotional rewards.<br/>
✔ Increase customer engagement.<br/>
✔ Send loyalty campaigns.
"""

    else:

        recommendation="""
✔ Continue quality customer service.<br/>
✔ Maintain customer engagement.<br/>
✔ Offer regular loyalty benefits.
"""

    elements.append(
        Paragraph(
            recommendation,
            body_style
        )
    )

    elements.append(Spacer(1,30))

    # =====================
    # Footer
    # =====================

    footer = Paragraph(
        "GENERATED BY<br/>"
        "Bank Customer Churn Prediction System — 2026",
        footer_style
    )

    elements.append(footer)

    # =====================
    # Dark page background + gold top bar (drawn behind the flowables)
    # =====================

    def draw_background(canvas, doc):
        canvas.saveState()
        page_width, page_height = doc.pagesize

        canvas.setFillColor(colors.HexColor(PAPER))
        canvas.rect(0, 0, page_width, page_height, stroke=0, fill=1)

        canvas.setFillColor(colors.HexColor(GOLD))
        canvas.rect(0, page_height - 4, page_width, 4, stroke=0, fill=1)

        canvas.restoreState()

    doc.build(
        elements,
        onFirstPage=draw_background,
        onLaterPages=draw_background
    )

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
        return redirect(url_for("signin"))

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
        return redirect(url_for("signin"))

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
        return redirect(url_for("signin"))

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
