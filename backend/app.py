from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager
import joblib
import os
from datetime import datetime
import csv
import smtplib
from email.mime.text import MIMEText
from backend.transactions.routes import transactions_bp
from backend.auth.routes import auth_bp, login_manager

app = Flask(
    __name__,
    template_folder='frontend/templates',
    static_folder='frontend/static'
)

# Secret key for session management
app.secret_key = 'your_secret_key_here'

# Register login manager and blueprint
login_manager.init_app(app)
app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp, url_prefix='/transactions')

# ✅ Root route redirect
@app.route('/')
def home():
    return redirect('/transactions/submit')

# Load model and encoder
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
model = joblib.load(os.path.join(model_path, 'fraud_model.pkl'))
encoder = joblib.load(os.path.join(model_path, 'location_encoder.pkl'))

# Attach model and encoder to app config for blueprint access
app.config['MODEL'] = model
app.config['ENCODER'] = encoder

import smtplib
from email.mime.text import MIMEText

# SendGrid configuration
SENDGRID_USERNAME = "apikey"  # This stays as 'apikey'
SENDGRID_API_KEY = "your_actual_sendgrid_api_key"
EMAIL_SENDER = "delightmhlanga82@gmail.com"  # Must be verified in SendGrid
EMAIL_RECEIVER = "delightdube341@gmail.com"

def send_email_alert(user_id, amount, location):
    subject = "🚨 Fraud Alert"
    body = f"Fraud detected!\nUser: {user_id}\nAmount: {amount}\nLocation: {location}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP("smtp.sendgrid.net", 587) as server:
            server.starttls()
            server.login(SENDGRID_USERNAME, SENDGRID_API_KEY)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("✅ Email alert sent successfully.")
    except Exception as e:
        print(f"❌ Email alert failed: {e}")


API_KEY = "sk_live_9f8d3a2b7c4e1x9z"
@app.route('/predict', methods=['POST'])
def predict():
    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {API_KEY}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    try:
        user_id = data.get('user_id', 'anonymous')
        amount = data.get('amount', 0)
        location = data.get('location', '')

        location_encoded = encoder.transform([location])[0]
        prediction = model.predict([[amount, location_encoded]])[0]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "FRAUD" if prediction else "NORMAL"

        # Save to fraud_log.csv (inside backend folder)
        csv_path = os.path.join(os.path.dirname(__file__), 'fraud_log.csv')
        log_entry = [timestamp, user_id, amount, location, status]
        with open(csv_path, "a", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(log_entry)

        if prediction:
            print(f"[ALERT] Fraud detected! User: {user_id}, Amount: {amount}, Location: {location}")
            send_email_alert(user_id, amount, location)
           
        return jsonify({
            'is_fraud': bool(prediction),
            'message': 'Fraudulent transaction' if prediction else 'Transaction appears normal'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    data = []
    try:
        # Load fraud_log.csv from backend folder
        csv_path = os.path.join(os.path.dirname(__file__), 'fraud_log.csv')
        with open(csv_path, "r") as csvfile:
            reader = csv.reader(csvfile)
            data = list(reader)
        print(f"✅ Loaded {len(data)} rows from fraud_log.csv")
    except Exception as e:
        print(f"❌ Error loading fraud log: {e}")
    return render_template("dashboard.html", data=data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)