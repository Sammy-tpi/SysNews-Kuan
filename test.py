import feedparser

rss_urls = [
    "https://fintechnews.hk/feed/",
    "https://www.blocktempo.com/feed/",
    "https://coinpost.jp/?feed=rss2",
    "https://www.coinness.com/rss",
    "https://e27.co/index_wp.php/feed",
    "https://asiatimes.com/feed",
    "https://www.digitalnewsasia.com/rss.xml",
    "https://www.eastasiaforum.org/feed",
    "https://asianbusinessdaily.com/feed",
    "https://www.fintechfutures.com/keyword/asia/feed/"
    "https://chinatechnews.com/feed",
    "https://www.techinasia.com/tag/china/feed",
    "https://blockchain.news/rss",
    "https://36kr.com/feed",
    "https://www.panewslab.com/rss",
    "https://coinhero.hk/feed",
    "https://www.investhk.gov.hk/news/feed",
    "https://fintechnews.hk/fintechtaiwan/feed/",
    "https://coinpost.jp/?feed=rss2",
    "https://www.japantimes.co.jp/news/asia-pacific/rss",
    "https://bittimes.net/rss",
    "https://decenter.kr/rss",
    "https://www.koreaittimes.com/rss.xml",
    "https://fintechnews.hk/fintechkorea/feed/",
    "https://asiafinancial.com/feed",
    "https://thediplomat.com/feed",
    "https://coin98.net/rss",
    "https://siamblockchain.com/feed",
    "https://bitpinas.com/feed",
    "https://crypto.news/tag/asia/feed",
    "https://cointelegraph.com/rss",
    "https://www.binance.com/en/square/hashtag/asia/rss",
    "https://asiapacificnews.net/rss",
    "https://www.fintechweekly.com/tags/artificial-intelligence/rss",
    "https://blog.chainalysis.com/rss",
    "https://www.reuters.com/rssFeed/asiaPacificNews",
    "https://apnews.com/rss/apf-asia-pacific",
    "https://www.eco-business.com/feeds/news",
    "https://news.gallup.com/topic/asia/feed"
]

for url in rss_urls:
    feed = feedparser.parse(url)
    status = "✅ Valid" if feed.entries else "❌ Invalid or Empty"
    print(f"{status} → {url} ({len(feed.entries)} entries)")
