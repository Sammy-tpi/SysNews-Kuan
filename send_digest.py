import yagmail
from datetime import datetime
from generate_digest import load_articles, generate_html

SENDER = "chenkuan.wu@tpisoftware.com"
PASSWORD = "chenkuan0330!"  # TODO: move to env var
RECIPIENT = "kuan940330@gmail.com"

JSON_PATH = "sample_articles.json"


def main():
    """Generate the digest HTML and email it."""
    # Use the generator from ``generate_digest.py`` which already defines a
    # clean multiline HTML template. This avoids inserting ``<br>`` tags in the
    # ``<style>`` block and keeps the CSS valid for email clients.
    articles = load_articles(JSON_PATH)
    html_content = generate_html(articles)

    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"📬 Polaris Daily Digest – {date_str}"

    yag = yagmail.SMTP(SENDER, PASSWORD)
    yag.send(to=RECIPIENT, subject=subject, contents=html_content)
    print("\u2705 Email sent.")

if __name__ == '__main__':
    main()
