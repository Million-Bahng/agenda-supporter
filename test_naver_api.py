import urllib.request
import urllib.parse
import json
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 경전회의 7개 아젠다 키워드 샘플
TEST_KEYWORDS = [
    "유통산업발전법",   # ① 정부 정책
    "동반성장 유통",    # ② 상생 협력
    "체험형 매장",      # ③ 마케팅 트렌드
    "감정노동자",       # ⑥ 소비자 보호
]

def search_news(keyword, display=5):
    enc_keyword = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/news.json?query={enc_keyword}&display={display}&sort=date"

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

    try:
        response = urllib.request.urlopen(request)
        result = json.loads(response.read().decode("utf-8"))
        return result.get("items", [])
    except Exception as e:
        return f"오류: {e}"

if __name__ == "__main__":
    for keyword in TEST_KEYWORDS:
        print(f"\n{'='*50}")
        print(f"[검색] 키워드: [{keyword}]")
        print('='*50)

        items = search_news(keyword, display=3)

        if isinstance(items, str):
            print(items)
            continue

        for i, item in enumerate(items, 1):
            title = item["title"].replace("<b>", "").replace("</b>", "")
            pub_date = item["pubDate"]
            link = item["link"]
            print(f"\n  {i}. {title}")
            print(f"     날짜: {pub_date}")
            print(f"     링크: {link}")
