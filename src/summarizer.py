import os
from typing import Dict

import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/free"
REQUEST_TIMEOUT_SECONDS = 20

SYSTEM_PROMPT = (
    "Bạn là chuyên gia phân tích pháp lý và kinh doanh tại Việt Nam. "
    "Hãy tóm tắt ngắn gọn bài báo sau thành đúng 3 gạch đầu dòng bằng tiếng Việt, "
    "tập trung vào tác động pháp lý, chính sách hoặc kinh doanh đối với doanh nghiệp và người dân. "
    "Không thêm lời mở đầu hay kết luận."
)


def _fallback_summary(description: str) -> str:
    """Return cleaned original description prefixed with [Tóm tắt gốc]."""
    clean_desc = (description or "").strip()
    if not clean_desc:
        return "[Tóm tắt gốc] Không có nội dung mô tả."
    return f"[Tóm tắt gốc] {clean_desc}"


def summarize_article(article: Dict[str, str]) -> str:
    """Summarize an article via OpenRouter API with mandatory graceful fallback."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    description = article.get("description", "")

    if not api_key:
        print("[Summarizer] OPENROUTER_API_KEY not found. Using fallback summary.")
        return _fallback_summary(description)

    title = article.get("title", "")
    user_content = f"Tiêu đề: {title}\nMô tả: {description}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if content:
            return content
        print("[Summarizer] Empty response from OpenRouter. Using fallback summary.")
        return _fallback_summary(description)
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        print(f"[Summarizer] OpenRouter API error ({exc}). Using fallback summary.")
        return _fallback_summary(description)
