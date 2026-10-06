import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(
    subject: str,
    html_body: str,
    plain_body: str,
    sender_email: str,
    sender_password: str,
    recipient: str,
) -> bool:
    """
    Sends a multipart/alternative email (HTML + plain-text fallback) via SMTP.
    """
    if not sender_email or not sender_password or not recipient:
        print("[ERROR] Missing email configuration. Please ensure SENDER_EMAIL, SENDER_PASSWORD, and RECIPIENT_EMAIL are set.")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = recipient
    msg["Subject"] = subject

    # Plain text goes first (lowest priority fallback)
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    # HTML goes last (clients render the last part they support)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        print(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}...")
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()

        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Email successfully sent to {recipient}!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email to {recipient}: {e}")
        return False
