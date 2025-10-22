from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

# Load credentials from environment variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

def send_email(user_id, amount, location):
    subject = "🚨 Fraud Alert"
    html_content = f"""
    <p>A transaction has been flagged as potentially fraudulent:</p>
    <ul>
        <li><strong>User ID:</strong> {user_id}</li>
        <li><strong>Amount:</strong> ${amount}</li>
        <li><strong>Location:</strong> {location}</li>
    </ul>
    <p>Please review immediately.</p>
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
        print(f"✅ Email sent successfully. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Email failed: {e}")