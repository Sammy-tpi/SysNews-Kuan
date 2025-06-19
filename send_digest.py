import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv
from generate_digest import load_articles, generate_html

# --- Load environment variables ---
load_dotenv()
SENDER = os.getenv("DIGEST_SENDER")
PASSWORD = os.getenv("DIGEST_PASSWORD")
RECIPIENTS_RAW = os.getenv("DIGEST_RECIPIENT", "")
RECIPIENTS = [email.strip() for email in RECIPIENTS_RAW.split(",") if email.strip()]

if not all([SENDER, PASSWORD]) or not RECIPIENTS:
    raise RuntimeError("❌ Missing sender, password, or recipient(s) in .env")

# --- JSON path ---
JSON_PATH = "data/news_data.json"

def main():
    articles = load_articles(JSON_PATH)
    html_content = generate_html(articles)
    date_str = datetime.now().strftime("%Y-%m-%d")

    # --- Compose email ---
    msg = EmailMessage()
    msg["Subject"] = f"📬 Polaris Daily Digest – {date_str}"
    msg["From"] = SENDER
    msg["To"] = ", ".join(RECIPIENTS)  # visible To: header
    msg.set_content("This email requires an HTML-capable client.")
    msg.add_alternative(html_content, subtype="html")

    # --- Send email ---
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER, PASSWORD)
            # ✅ true recipient list here
            smtp.sendmail(SENDER, RECIPIENTS, msg.as_string())

    except smtplib.SMTPAuthenticationError:
        raise RuntimeError("❌ Gmail authentication failed — check app password.")
    except Exception as exc:
        raise RuntimeError(f"❌ Failed to send email: {exc}") from exc

    print("✅ Email sent to:", ", ".join(RECIPIENTS))


if __name__ == "__main__":
    main()
