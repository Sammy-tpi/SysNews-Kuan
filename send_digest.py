import yagmail
from datetime import datetime

SENDER = "chenkuan.wu@tpisoftware.com"
PASSWORD = "chenkuan0330!"  # TODO: move to env var
RECIPIENT = "kuan940330@gmail.com"

def main():
    date_str = datetime.now().strftime('%Y-%m-%d')
    subject = f"📬 Polaris Daily Digest – {date_str}"
    with open('digest.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    yag = yagmail.SMTP(SENDER, PASSWORD)
    yag.send(to=RECIPIENT, subject=subject, contents=html_content)
    print("\u2705 Email sent.")

if __name__ == '__main__':
    main()
