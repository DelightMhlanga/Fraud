import smtplib
from email.mime.text import MIMEText

def send_email(user_id, amount, location):
    sender = "delightmhlanga82@gmail.com"
    recipient = "delightdube341@gmail.com"
    password = "lfsiycvdpsazudgk"
    subject = "🚨 Fraud Alert"
    body = f"""
    A transaction has been flagged as potentially fraudulent:

    User ID: {user_id}
    Amount: ${amount}
    Location: {location}

    Please review immediately.
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            print("✅ Email sent successfully")
    except Exception as e:
        print("❌ Email failed:", e)