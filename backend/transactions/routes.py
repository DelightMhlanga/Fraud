from flask import Blueprint, render_template, request, redirect, url_for, Response
import csv
import os
import joblib
from datetime import datetime
from collections import Counter
import pdfkit
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
from backend.transactions.email import send_email
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


transactions_bp = Blueprint('transactions', __name__, template_folder='templates')

# Load model and encoder
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models'))
model = joblib.load(os.path.join(model_path, 'fraud_model.pkl'))
encoder = joblib.load(os.path.join(model_path, 'location_encoder.pkl'))

# ✅ Suspend Account
def suspend_account(user_id):
    suspend_path = os.path.join(os.path.dirname(__file__), '..', 'suspended_users.csv')
    with open(suspend_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

# ✅ Log Transaction
def log_transaction(timestamp, user_id, amount, location, status):
    log_path = os.path.join(os.path.dirname(__file__), '..', 'transaction_log.csv')
    with open(log_path, "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, user_id, amount, location, status])

# ✅ Verified Email and SMS Configuration

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

def send_verification_email(user_id, amount, location, timestamp):
    subject = "🚨 Transaction Verification Needed"
    html_content = f"""
    <p>A transaction was flagged as potentially fraudulent:</p>
    <ul>
        <li><strong>User:</strong> {user_id}</li>
        <li><strong>Amount:</strong> ${amount}</li>
        <li><strong>Location:</strong> {location}</li>
        <li><strong>Time:</strong> {timestamp}</li>
    </ul>
    <p>Please confirm:</p>
    <p><a href="https://fraud-wkgv.onrender.com/verify?user_id={user_id}&amount={amount}&location={location}&timestamp={timestamp}&confirm=yes">✅ Yes, it's me</a></p>
    <p><a href="https://fraud-wkgv.onrender.com/verify?user_id={user_id}&amount={amount}&location={location}&timestamp={timestamp}&confirm=no">❌ No, not me</a></p>
    """

    message = Mail(
        from_email=EMAIL_SENDER,
        to_emails=EMAIL_RECEIVER,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"✅ Verification email sent. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending verification email: {e}")

# ✅ Submit Transaction Route
@transactions_bp.route('/submit', methods=['GET', 'POST'])
def submit_transaction():
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        amount_raw = request.form.get('amount', '').strip()
        location = request.form.get('location', '').strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not user_id or not amount_raw or not location:
            return "❌ All fields are required.", 400

        try:
            amount = float(amount_raw)
        except ValueError:
            return "❌ Invalid amount format.", 400

        # Scan immediately
        location_encoded = encoder.transform([location])[0]
        prediction = model.predict([[amount, location_encoded]])[0]
        status = "FRAUD" if prediction else "NORMAL"

        if status == "FRAUD":
            try:  
                send_verification_email(user_id, amount, location, timestamp)
                send_email(user_id, amount, location)  # ✅ Added email alert here
            except Exception as e:
                print(f"❌ Error sending fraud alerts: {e}")

        log_transaction(timestamp, user_id, amount, location, status)

        # Show result message
        if status == "FRAUD":
            message = "🚨 Transaction pending for approval. A verification email has been sent."
        else:
            message = "✅ Transaction successful."

        return render_template('submit_result.html',
                               user_id=user_id,
                               amount=amount,
                               location=location,
                               timestamp=timestamp,
                               message=message)

    return render_template('submit.html')

@transactions_bp.route('/review')
def review():
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'pending_transactions.csv')
    transactions = []
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            transactions.append(row)
    return render_template('review.html', transactions=transactions)

@transactions_bp.route('/scan', methods=['POST'])
def scan():
    user_id = request.form.get('user_id', '').strip()
    amount_raw = request.form.get('amount', '').strip()
    location = request.form.get('location', '').strip()
    decision = request.form.get('decision', 'scan')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Validate inputs
    if not user_id or not amount_raw or not location:
        return "❌ All fields are required.", 400

    try:
        amount = float(amount_raw)
    except ValueError:
        return "❌ Invalid amount format.", 400

    # Continue with fraud detection logic...

    if decision == "scan":
        location_encoded = encoder.transform([location])[0]
        prediction = model.predict([[amount, location_encoded]])[0]
        status = "FRAUD" if prediction else "NORMAL"
    elif decision == "approve":
        status = "APPROVED"
    elif decision == "deny":
        status = "DENIED"
    else:
        status = "UNKNOWN"

    if status == "FRAUD":
        try:
          
            # Email verification
            send_verification_email(user_id, amount, location, timestamp)

        except Exception as e:
            print(f"❌ Error sending fraud alerts: {e}")

    log_transaction(timestamp, user_id, amount, location, status)
    return redirect(url_for('transactions.review'))

@transactions_bp.route('/verify')
def verify():
    user_id = request.args.get('user_id')
    amount_raw = request.args.get('amount')
    location = request.args.get('location')
    timestamp = request.args.get('timestamp')
    confirm = request.args.get('confirm')

    try:
        amount = float(amount_raw)
    except (ValueError, TypeError):
        return "❌ Invalid amount format.", 400

    if confirm == "yes":
        status = "APPROVED"
    else:
        status = "DENIED"
        suspend_account(user_id)

    log_transaction(timestamp, user_id, amount, location, status)

    return render_template('verify_result.html',
                           user_id=user_id,
                           amount=amount,
                           location=location,
                           timestamp=timestamp,
                           status=status,
                           message=f"Transaction has been {status.lower()}.")

@transactions_bp.route('/report')
def report():
    log_path = os.path.join(os.path.dirname(__file__), '..', 'transaction_log.csv')
    report_data = []
    summary = {
        'total': 0,
        'fraud': 0,
        'approved': 0,
        'denied': 0,
        'normal': 0
    }

    status_filter = request.args.get('status', '').upper()
    date_filter = request.args.get('date', '')

    fraud_counter = Counter()

    try:
        with open(log_path, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 5:
                    continue
                timestamp, user_id, amount, location, status = row
                if status_filter and status.upper() != status_filter:
                    continue
                if date_filter and not timestamp.startswith(date_filter):
                    continue
                report_data.append(row)
                summary['total'] += 1
                status_upper = status.upper()
                if status_upper == "FRAUD":
                    summary['fraud'] += 1
                    date_only = timestamp.split(" ")[0]
                    fraud_counter[date_only] += 1
                elif status_upper == "APPROVED":
                    summary['approved'] += 1
                elif status_upper == "DENIED":
                    summary['denied'] += 1
                elif status_upper == "NORMAL":
                    summary['normal'] += 1
    except Exception as e:
        print(f"❌ Error loading report: {e}")

    fraud_dates = sorted(fraud_counter.keys())
    fraud_counts = [fraud_counter[date] for date in fraud_dates]

    return render_template('report.html',
                           report=report_data,
                           summary=summary,
                           fraud_dates=fraud_dates,
                           fraud_counts=fraud_counts)

@transactions_bp.route('/report/pdf')
def report_pdf():
    log_path = os.path.join(os.path.dirname(__file__), '..', 'transaction_log.csv')
    report_data = []
    summary = {'total': 0, 'fraud': 0, 'approved': 0, 'denied': 0, 'normal': 0}

    try:
        with open(log_path, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 5:
                    continue
                report_data.append(row)
                status = row[4].strip().upper()
                summary['total'] += 1
                if status == "FRAUD":
                    summary['fraud'] += 1
                elif status == "APPROVED":
                    summary['approved'] += 1
                elif status == "DENIED":
                    summary['denied'] += 1
                elif status == "NORMAL":
                    summary['normal'] += 1
    except Exception as e:
        print(f"❌ Error loading report: {e}")
        report_data = []
        summary = {'total': 0, 'fraud': 0, 'approved': 0, 'denied': 0, 'normal': 0}

    rendered = render_template('report.html',
                               report=report_data,
                               summary=summary,
                               fraud_dates=[],
                               fraud_counts=[])
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    pdf = pdfkit.from_string(rendered, False, configuration=config)
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment;filename=report.pdf"})