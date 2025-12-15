import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.setting import GMAIL_PASSWORD

# Gmail config
GMAIL_USER = "jesmine0820@gmail.com"
GMAIL_PASSWORD = GMAIL_PASSWORD

def generate_otp():
    return ''.join(str(random.randint(0, 9)) for _ in range(6))


def send_otp(to_email):
    otp = generate_otp()

    subject = "Your OTP Code"
    body = f"""
Hello,

Your OTP code is: {otp}

This code is valid for 10 minutes.
If you did not request this, please ignore this email.

Regards,
Security Team
IELTS Listening Module Question Generator
"""

    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)

        print(f"[SUCCESS] OTP sent to {to_email}")
        return otp

    except Exception as e:
        print(f"[ERROR] Failed to send OTP: {e}")
        return None