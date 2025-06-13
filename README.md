# NewsRender

This repository contains utilities for generating and sending a daily news digest.

## Configuration

Email credentials are loaded from environment variables using `python-dotenv`.
Create a `.env` file in the project root containing:

```
DIGEST_SENDER=<your Gmail address>
DIGEST_PASSWORD=<your Gmail app password>
DIGEST_RECIPIENT=<recipient address>
```

Use a Gmail app password, which requires enabling two-factor authentication on your
account. Refer to Google's documentation if authentication fails.

## Usage

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Generate the HTML digest:

   ```bash
   python generate_digest.py
   ```

3. Send the digest via email:

   ```bash
   python send_digest.py
   ```
