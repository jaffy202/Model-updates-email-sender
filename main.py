import os
from datetime import datetime
from pathlib import Path
# pyrefly: ignore [missing-import]
from llm_scraping import get_latest_model_updates
from email_sender import send_email
from email_formatter import parse_models, build_html_email, build_plain_text_email


OUTPUT_FILE = Path(__file__).parent / "last_output.txt"
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")


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

        # Build formatted email bodies
        models = parse_models(new_output)
        date_str = datetime.now().strftime("%B %d, %Y")
        html_body = build_html_email(models, date_str)
        plain_body = build_plain_text_email(models, date_str)

        # Send email
        subject = f"🤖 New LLM Model Updates — {date_str}"
        send_email(
            subject=subject,
            html_body=html_body,
            plain_body=plain_body,
            sender_email=SENDER_EMAIL,
            sender_password=SENDER_PASSWORD,
            recipient=RECIPIENT_EMAIL,
        )
    else:
        print("\n[NO CHANGE] Latest updates match the previous run in last_output.txt.")


if __name__ == "__main__":
    main()
