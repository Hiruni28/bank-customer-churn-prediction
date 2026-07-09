from flask import Flask, render_template, request, redirect, url_for, session
import numpy as np
import joblib
import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

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

    return render_template(
    "dashboard.html",
    user=session["user"]
)

@app.route("/prediction")
def prediction():

    if "user" not in session:

        return redirect(url_for("home"))

    return render_template(
        "index.html",
        user=session["user"]
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

    if probability >= 0.5:
        prediction = "Customer is likely to churn."
    else:
        prediction = "Customer is not likely to churn."

    return render_template(
    "index.html",
    user=session["user"],
    prediction=prediction,
    probability=round(probability * 100, 2)
)


if __name__ == "__main__":
    app.run(debug=True)