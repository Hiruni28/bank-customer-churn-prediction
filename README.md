# 🏦 Bank Customer Churn Prediction System

A Machine Learning web application built with **Flask** that predicts whether a bank customer is likely to churn (leave the bank). The system provides risk classification, interactive dashboards, prediction history, reports, and downloadable PDF reports.

---

## 📌 Project Overview

Customer churn is one of the major challenges faced by banks. This system uses a trained Machine Learning model to analyze customer information and predict the probability of customer churn.

Based on the prediction, customers are classified into:

- 🔴 High Risk
- 🟡 Medium Risk
- 🟢 Low Risk

The application also stores prediction history, generates reports, and allows users to download professional PDF reports.

---

## ✨ Features

- 🔐 Google OAuth Login
- 🤖 Machine Learning Churn Prediction
- 📊 Probability Score
- 🔴 High / 🟡 Medium / 🟢 Low Risk Classification
- 💡 Customer Retention Recommendations
- 📈 Dashboard Analytics
- 📜 Prediction History
- 📊 Reports with Charts
- 📄 PDF Report Generation
- 💾 SQLite Database
- 🎨 Responsive Bootstrap UI

---

## 🛠️ Technologies Used

### Programming Language

- Python

### Machine Learning

- LightGBM
- Scikit-learn
- NumPy
- Joblib

### Backend

- Flask

### Frontend

- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- Chart.js

### Database

- SQLite

### Authentication

- Google OAuth

### PDF Generation

- ReportLab

### Development Tools

- Visual Studio Code
- Git
- GitHub

---

## 📂 Project Structure


bank-customer-churn-prediction/
│
├── static/
│   ├── dashboard.css
│   ├── history.css
│   ├── home.css
│   ├── navbar.css
│   ├── reports.css
│   └── style.css
│
├── templates/
│   ├── dashboard.html
│   ├── history.html
│   ├── home.html
│   ├── index.html
│   ├── login.html
│   ├── navbar.html
│   └── reports.html
│
├── app.py
├── database.py
├── bank.db
├── bank_churn_model.pkl
├── scaler.pkl
├── requirements.txt
├── README.md
├── .gitignore
├── .env
└── venv/
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/Hiruni28/bank-customer-churn-prediction.git
```

### Navigate to the project

```bash
cd bank-customer-churn-prediction
```

### Create virtual environment

```bash
python -m venv venv
```

### Activate virtual environment

Windows

```bash
venv\Scripts\activate
```

Mac/Linux

```bash
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root.

```text
SECRET_KEY=your_secret_key

GOOGLE_CLIENT_ID=your_google_client_id

GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Run the application

```bash
python app.py
```

Open your browser and visit

```
http://127.0.0.1:5000
```

---

## 📊 Machine Learning Model

The prediction model was developed using the **LightGBM (Light Gradient Boosting Machine)** algorithm. Before training, customer data was preprocessed using **Scikit-learn**, including feature scaling and one-hot encoding for categorical variables.

The trained model predicts the probability of customer churn and classifies customers into three risk categories:

- 🔴 High Risk
- 🟡 Medium Risk
- 🟢 Low Risk

The trained model is stored as:

- `bank_churn_model.pkl`

The feature scaler is stored as:

- `scaler.pkl`

### Input Features

- Credit Score
- Age
- Tenure
- Balance
- Number of Products
- Has Credit Card
- Active Member
- Estimated Salary
- Gender
- Geography

### Output

- Churn Probability
- Risk Level
- Customer Recommendation

---

## 📄 PDF Report

The system automatically generates a professional PDF report including:

- Customer Name
- Email
- Date & Time
- Churn Probability
- Risk Level
- Prediction Result
- Recommendations

---

## 📈 Dashboard

The dashboard displays:

- Total Predictions
- High Risk Customers
- Medium Risk Customers
- Low Risk Customers
- Interactive Charts
- Prediction Reports

---

## 🔒 Authentication

Users securely sign in using Google OAuth authentication before accessing the system.

---

## 👨‍💻 Developer

**Hiruni Parindhya**

BSc (Hons) Computing & Software Engineering

---

## 📜 License

This project was developed for educational purposes as part of a Machine Learning coursework project.