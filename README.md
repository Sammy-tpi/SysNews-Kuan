# NewsRender

**NewsRender** is a Python-powered pipeline that delivers a **daily bilingual (English + Traditional Chinese)** digest of the most relevant AI, FinTech, and startup news. It pulls content from curated **RSS/RSSHub feeds** and the **EventRegistry API**, filters it using custom keywords, ranks and summarizes with **LLM models**, and sends out a clean, branded HTML email to subscribed recipients.

---

## ✨ Features

* ✅ Multi-source news aggregation (RSS, and EventRegistry)
* ✅ Region and topic-based classification
* ✅ LLM-powered relevance filtering and bilingual summarization
* ✅ Responsive HTML digest rendering with custom styling
* ✅ Email delivery with Gmail SMTP
* ✅ Automated daily scheduling via GitHub Actions

---

## 📁 Project Structure

```
NewsRender/
├── config/                    # Source and keyword configuration
│   ├── sources.json           # RSS & API sources by region and topic
│   └── keywords.json          # Keyword list for filtering and scoring
├── data/                      # Intermediate and final JSON outputs
├── templates/                 # HTML email templates (Jinja2)
├── .github/workflows/         # GitHub Actions scheduler
├── main.py                    # Full pipeline runner
├── fetch_rss_articles.py      # Async RSS fetcher
├── fetch_newsapi_ai.py        # EventRegistry API fetcher
├── filter_articles_by_date.py # Keeps articles from the past 2 days
├── filter_relevance_gpt.py    # GPT-based topic relevance filter
├── classify_articles_gpt.py   # Categorize, score, and label region
├── select_top_articles.py     # Pick top article for each region/category
├── summarize_articles.py      # Generate Traditional Chinese summaries
├── generate_digest.py         # Render HTML digest with Jinja2
└── send_digest.py             # Send email via Gmail
```

---

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```env
DIGEST_SENDER=your_email@gmail.com
DIGEST_PASSWORD=your_gmail_app_password
DIGEST_RECIPIENT=recipient1@example.com,recipient2@example.com
OPENAI_API_KEY=your_openai_api_key
NEWSAPI_AI_KEY=your_eventregistry_api_key
```

> ✅ **Note:** Gmail requires an [App Password](https://support.google.com/accounts/answer/185833?hl=en) if 2FA is enabled.

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the full pipeline

```bash
python main.py
```

This executes the following steps:

1. `fetch_newsapi_ai.py` — Query EventRegistry for AI/FinTech articles.
2. `fetch_rss_articles.py` — Async fetch from RSS/RSSHub sources using `config/sources.json`.
3. `filter_articles_by_date.py` — Keep articles published in the last two days.
4. `filter_relevance_gpt.py` — Remove articles unrelated to AI, FinTech, or Blockchain.
5. `classify_articles_gpt.py` — Categorize, score, and tag the region.
6. `select_top_articles.py` — Pick top article per category and region.
7. `summarize_articles.py` — Generate Traditional Chinese summaries.
8. `validate_news_data.py` — Validate format and remove duplicates.
9. `generate_digest.py` — Render `digest.html` using a clean Jinja2 template.
10. `send_digest.py` — Email the digest via Gmail SMTP.

Intermediate results are stored in the `data/` folder.

---

## 🛠 Customization

### Modify Sources

Edit `config/sources.json` to update or add RSS feeds:

```json
{
  "name": "TechCrunch",
  "region": "Global",
  "topics": ["AI", "FinTech"],
  "source_type": "rss",
  "full_text": true
}
```

### Update Keywords

Edit `config/keywords.json` to define keyword filters in multiple languages (EN/ZH):

```json
{
  "keywords": ["AI", "演算法交易", "智能合約", "Robo-advisor", "金融科技"]
}
```

---

## 🖼 Sample Output

The output is a responsive, visually clean **HTML digest** with 6 cards:

* 3 regions: 🌍 Global, 🇹🇼 East Asia
* 3 categories: General Tech, Applied AI in Finance, Blockchain & Crypto

Each card includes:

* ✅ Article title
* ✅ Source & time
* ✅ English summary (LLM-generated)
* ✅ Traditional Chinese summary (translated)
* ✅ Link to full article

---

## ⏱️ Automation

This project includes a GitHub Actions workflow that runs `main.py` daily:

```
.github/workflows/daily.yml
```

You can enable it by committing a valid `.env` (excluded from Git) on your deployment server or GitHub Secrets.

---

## 📜 License

This project is licensed under the MIT License.
