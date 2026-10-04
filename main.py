import os
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# pyrefly: ignore [missing-import]
from llm_scraping import get_latest_model_updates


OUTPUT_FILE = Path(__file__).parent / "last_output.txt"
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(subject: str, body: str, recipient: str = None) -> bool:
    """
    Sends an email using SMTP credentials.
    """
    recipient = recipient or RECIPIENT_EMAIL
    if not SENDER_EMAIL or not SENDER_PASSWORD or not recipient:
        print("[ERROR] Missing email configuration. Please ensure SENDER_EMAIL, SENDER_PASSWORD, and RECIPIENT_EMAIL are set.")
        return False

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        print(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}...")
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()

        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email successfully sent to {recipient}!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email to {recipient}: {e}")
        return False


def main():
    print("Fetching latest model updates...")
    new_output = get_latest_model_updates()
    
    # Read previous output if last_output.txt exists
    last_output = None
    if OUTPUT_FILE.exists():
        try:
            last_output = OUTPUT_FILE.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[WARNING] Could not read existing {OUTPUT_FILE.name}: {e}")

    # Check whether output has changed or last_output.txt does not exist
    has_changed = (last_output is None) or (new_output.strip() != last_output.strip())

    if has_changed:
        print("\n[UPDATE DETECTED] New updates found or initial run.")
        
        # Save output to last_output.txt
        OUTPUT_FILE.write_text(new_output, encoding="utf-8")
        print(f"Updated contents saved to: {OUTPUT_FILE}")

        # Send email
        subject = "New LLM Model Updates"
        send_email(subject=subject, body=new_output, recipient=RECIPIENT_EMAIL)
    else:
        print("\n[NO CHANGE] Latest updates match the previous run in last_output.txt.")


if __name__ == "__main__":
    main()
