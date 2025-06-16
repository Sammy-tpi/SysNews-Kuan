import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv
from generate_digest import load_articles, generate_html

# Load email credentials from environment variables
load_dotenv()
SENDER = os.getenv("DIGEST_SENDER")
PASSWORD = os.getenv("DIGEST_PASSWORD")
RECIPIENT = os.getenv("DIGEST_RECIPIENT")

if not all([SENDER, PASSWORD, RECIPIENT]):
    raise RuntimeError(
        "Missing DIGEST_SENDER, DIGEST_PASSWORD or DIGEST_RECIPIENT in environment"
    )

# ✅ 正確的 JSON 檔案位置
JSON_PATH = "data/news_data.json"

def main():
    """Generate the digest HTML and email it."""
    articles = load_articles(JSON_PATH)
    html_content = generate_html(articles)

    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"📬 Polaris Daily Digest – {date_str}"

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER
    msg['To'] = RECIPIENT
    msg.set_content('This email requires an HTML capable client.')
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER, PASSWORD)
            smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            "❌ Authentication failed. Double-check Gmail & app password."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"❌ Failed to send email: {exc}") from exc

    print("✅ Email sent.")

if __name__ == '__main__':
    main()
