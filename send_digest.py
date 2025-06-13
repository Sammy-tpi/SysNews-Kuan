import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv
from generate_digest import load_articles, generate_html

load_dotenv()

SENDER = os.getenv("DIGEST_SENDER")
PASSWORD = os.getenv("DIGEST_PASSWORD")
RECIPIENT = os.getenv("DIGEST_RECIPIENT")

JSON_PATH = "news_data.json"


def main():
    """Generate the digest HTML and email it."""
    # Use the generator from ``generate_digest.py`` which already defines a
    # clean multiline HTML template. This avoids inserting ``<br>`` tags in the
    # ``<style>`` block and keeps the CSS valid for email clients.
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

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER, PASSWORD)
        smtp.send_message(msg)
    print("\u2705 Email sent.")

if __name__ == '__main__':
    main()
