# NewsRender

NewsRender generates a bilingual technology digest. It collects news from RSS feeds and the EventRegistry API, filters and classifies the articles with OpenAI, and emails a daily HTML summary.

## Configuration

Create a `.env` file in the project root. The application reads credentials with `python-dotenv`:

```
DIGEST_SENDER=<your Gmail address>
DIGEST_PASSWORD=<your Gmail app password>
DIGEST_RECIPIENT=<recipient1@example.com,recipient2@example.com>
OPENAI_API_KEY=<your OpenAI API key>
NEWSAPI_AI_KEY=<your EventRegistry key>
```

Gmail requires an app password (two‑factor authentication must be enabled). Multiple recipients are comma separated.

## Installation

```bash
pip install -r requirements.txt
```

## Running the pipeline

Execute all steps with:

```bash
python main.py
```

`main.py` runs the following scripts in order:

1. `fetch_newsapi_ai.py` – query EventRegistry for matching articles.
2. `fetch_rss_articles.py` – asynchronously pull articles from RSS/RSSHub sources in `config/sources.json`.
3. `filter_articles_by_date.py` – keep only items from the last two days.
4. `filter_with_gpt.py` – classify relevance, topic and region using OpenAI.
5. `select_top_articles.py` – pick the highest‑scoring article for each region and category.
6. `summarize_articles.py` – generate a Traditional Chinese summary for each top article.
7. `validate_news_data.py` – ensure all categories exist and remove duplicates.
8. `generate_digest.py` – render `digest.html` using `templates/digest_single_column.html`.
9. `send_digest.py` – email the digest.

Intermediate JSON files are stored in the `data/` directory.

## Customising sources and keywords

- `config/sources.json` lists RSS and RSSHub feeds grouped by region.
- `config/keywords.json` contains the keywords used to score and filter articles.

Edit these files to adapt the digest to your needs.

## GitHub Actions

`.github/workflows/daily.yml` runs `python main.py` on a schedule, allowing the digest to be created automatically.

