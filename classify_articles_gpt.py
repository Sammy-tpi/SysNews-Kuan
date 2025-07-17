"""Second-layer GPT classifier.

This module runs after ``filter_relevance_gpt.py``. It assigns a
human-readable category and region label to each article. The results
are stored for later summarization.
"""

import json
import os
import re
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List, Any

INPUT_FILE = "data/classified_articles.json"
OUTPUT_ALL_FILE = "data/news_data.json"
CATEGORY_DIR = "data/categorized"

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

CATEGORY_MAPPING = {
    "Research": "Research",
    "Infrastructure": "Infrastructure",
    "FinTech": "FinTech",
    "Startup": "Startup",
}

STANDARD_CATEGORIES = list(set(CATEGORY_MAPPING.values()))


REGIONS = ["Global", "Taiwan"]

MAX_CONTENT_TOKENS = 1000  # Adjust based on your model's token limit


def truncate_text(text: str, max_tokens: int = MAX_CONTENT_TOKENS) -> str:
    """截斷文本到指定的最大 token 數，避免超出模型限制。"""
    words = text.split()
    return " ".join(words[:max_tokens])

def load_prompt(path: str) -> str:
    """從檔案載入 Prompt 模板。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

VERSION = "v2.1"
PROMPT_PATH = f"prompts/classify_articles_{VERSION}.txt" # 確保這個路徑指向你的新 Prompt 檔案
PROMPT_TEMPLATE = load_prompt(PROMPT_PATH)


def load_articles(path: str) -> List[Dict[str, Any]]:
    """載入待分類的文章列表。"""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON in {path}")


semaphore = asyncio.Semaphore(3) # 限制併發請求數量，避免 API 速率限制


def _parse_response(text: str) -> Dict[str, Any]:
    """解析模型的回應文本，提取類別和地區資訊。"""
    raw_text = text
    try:
        # 嘗試找到 JSON 物件，通常模型會將 JSON 包裹在 ```json ... ``` 中
        match = re.search(r"\{[^{}]*\}", raw_text, re.DOTALL)
        if match:
            raw_text = match.group(0)
        else:
            # 如果沒有找到 JSON 包裹，則嘗試移除常見的 Markdown 標記
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw_text)
        # 模型應返回 "category" 和 "region"
        return {
            "category": data.get("category", ""),
            "region": data.get("region", "Global"),
            "keep": data.get("keep", False) # 從模型回應中獲取 keep 屬性
        }
    except Exception as e:
        print("⚠️ 無法解析模型回應:", e)
        print("🧪 原始回應文本為:", repr(raw_text))
        # 返回預設值，確保程式不會崩潰
        return {"category": "", "region": "Global", "keep": False}


async def classify_article(article: Dict[str, Any]) -> Dict[str, Any] | None:
    """對單篇文章進行分類。"""
    title = article.get("title", "")
    content = article.get("content") or article.get("description", "")
    if not title or not content:
        return None # 如果沒有標題或內容則跳過

    short_content = truncate_text(content)
    # 將文章標題和截斷後的內容組合成 Prompt
    prompt = f"{PROMPT_TEMPLATE.strip()}\n\nTitle: {title}\n\n Content:\n{short_content}"

    async with semaphore: # 使用 semaphore 限制併發請求
        try:
            # 異步呼叫模型進行內容生成
            resp = await model.generate_content_async(prompt)
            text = resp.text
            print("📩 模型原始回應:", text)
            return _parse_response(text)
        except Exception as e:
            print(f"❌ 請求期間發生例外: {e}")
            return None # 發生錯誤時返回 None


async def main_async() -> None:
    """主異步函數，負責載入、分類、儲存文章。"""
    articles = load_articles(INPUT_FILE)
    os.makedirs(CATEGORY_DIR, exist_ok=True)

    # 初始化分組字典，使用 STANDARD_CATEGORIES
    grouped = {region: {cat: [] for cat in STANDARD_CATEGORIES} for region in REGIONS}
    results: List[Dict[str, Any]] = [] # 儲存所有分類後的文章

    valid_articles: List[Dict[str, Any]] = []
    for art in articles:
        title = art.get("title", "")
        content = art.get("content") or art.get("description", "")
        if not title or not content:
            continue
        valid_articles.append(art)

    # 併發執行所有文章的分類任務
    tasks = [classify_article(art) for art in valid_articles]
    responses = await asyncio.gather(*tasks)

    # 定義你認為是 AI 相關的類別列表
    AI_RELATED_CATEGORIES = ["Research", "Infrastructure", "FinTech", "Startup"]
    # 這裡的列表需要根據你對「AI相關」的具體定義來調整
    # 如果你認為所有這四個類別都可能包含AI，那就保留，否則可以更具體
    # 例如，如果只有 Research 和 Infrastructure 的 AI 部分你感興趣，那就調整

    for art, result in zip(valid_articles, responses):
        if not result:
            continue

        raw_category_from_model = result.get("category", "")
        region = result.get("region", "Global")
        keep = result.get("keep", False)

        standardized_category = CATEGORY_MAPPING.get(raw_category_from_model, "Unknown")

        art["category"] = standardized_category
        art["region"] = region
        art["keep"] = keep

        # 新增的 AI 相關篩選邏輯
        # 只有當 keep 為 True 且 category 屬於 AI_RELATED_CATEGORIES 時才保留
        if keep and standardized_category in AI_RELATED_CATEGORIES:
            results.append(art)
            if region in grouped and standardized_category in grouped[region]:
                grouped[region][standardized_category].append(art)
            else:
                print(f"Warning: Article with category '{standardized_category}' or region '{region}' not added to grouped dictionary.")
        else:
            # 如果文章不保留（keep=false）或者不屬於 AI 相關類別，都將其排除
            if not keep:
                print(f"文章 '{art.get('title', '無標題')}' 因 keep=false 而被拒絕。")
            else: # 這表示 keep 是 true，但 category 不在 AI_RELATED_CATEGORIES 中
                print(f"文章 '{art.get('title', '無標題')}' 因類別 '{standardized_category}' 不屬於 AI 相關而被排除。")

    # 將所有已分類並保留的文章寫入一個總檔案
    with open(OUTPUT_ALL_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 將文章按照地區和標準化類別分別寫入檔案
    for region, cats in grouped.items():
        for cat, items in cats.items(): # 這裡的 'cat' 已經是標準化後的類別
            # 只有當該類別下有文章時才建立檔案
            if items:
                # 確保檔案名稱是有效的，將空格替換為底線
                filename = f"{region}_{cat.replace(' ', '_')}.json"
                path = os.path.join(CATEGORY_DIR, filename)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
    print(
        f"已將 {len(results)} 篇已分類的文章寫入 {OUTPUT_ALL_FILE}"
    )
    print(f"✅ 成功分類並保留的文章數量: {len(results)}")


if __name__ == "__main__":
    asyncio.run(main_async())