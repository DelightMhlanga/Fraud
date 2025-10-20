from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager
import joblib
import os
from datetime import datetime
import csv
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
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

# API key for authentication
API_KEY = "your_secret_key_here"

# Email alert configuration
EMAIL_SENDER = "delightmhlanga82@gmail.com"
EMAIL_RECEIVER = "delightdube341@gmail.com"
EMAIL_PASSWORD = "lfsiycvdpsazudgk"

# SMS alert configuration
TWILIO_SID = "AC037ce44d192c69227320c8c599c69c16"
TWILIO_TOKEN = "a2cdd91236f6f9f3c2d0853613d01ede"
TWILIO_NUMBER = "+16204624903"
RECIPIENT_NUMBER = "+263786928638"

def send_email_alert(user_id, amount, location):
    subject = "🚨 Fraud Alert"
    body = f"Fraud detected!\nUser: {user_id}\nAmount: {amount}\nLocation: {location}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("✅ Email alert sent successfully.")
    except Exception as e:
        print(f"❌ Email alert failed: {e}")

def send_sms_alert(user_id, amount, location):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        message = client.messages.create(
            body=f"🚨 Fraud Alert!\nUser: {user_id}\nAmount: {amount}\nLocation: {location}",
            from_=TWILIO_NUMBER,
            to=RECIPIENT_NUMBER
        )
        print(f"📲 SMS sent: {message.sid}")
    except Exception as e:
        print(f"❌ SMS alert failed: {e}")

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
            send_sms_alert(user_id, amount, location)

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