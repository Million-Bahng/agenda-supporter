"""
네이버 뉴스 API 크롤러
경전회의 3개 섹션 구조에 맞춰 키워드 설계:
  섹션① 유통 주요기사 REVIEW  → 정부정책/마케팅트렌드/ESG/조직문화
  섹션② 사건사고 / 반면교사  → 경쟁사 갑질·위생·안전·윤리 위기사례
  섹션③ 당사 관련기사 REVIEW  → 현대백화점그룹 5개 계열사
  섹션④ 경쟁사 일반 동향     → 경쟁사 전략·실적·신규 서비스
"""
import urllib.request
import urllib.parse
import json
import os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# 주요 뉴스 도메인 → 매체명 매핑
DOMAIN_MAP = {
    "chosun": "조선일보", "donga": "동아일보", "joongang": "중앙일보",
    "hani": "한겨레", "khan": "경향신문", "ohmynews": "오마이뉴스",
    "hankyung": "한국경제", "mk": "매일경제", "mt": "머니투데이",
    "etnews": "전자신문", "zdnet": "ZDNet Korea", "bloter": "블로터",
    "yonhapnews": "연합뉴스", "yna": "연합뉴스", "newsis": "뉴시스",
    "news1": "뉴스1", "newspim": "뉴스핌", "edaily": "이데일리",
    "inews24": "아이뉴스24", "fnnews": "파이낸셜뉴스", "ajunews": "아주경제",
    "asiae": "아시아경제", "dailian": "데일리안", "wikitree": "위키트리",
    "sedaily": "서울경제", "sbs": "SBS", "kbs": "KBS", "mbc": "MBC",
    "jtbc": "JTBC", "ytn": "YTN", "mbn": "MBN", "channela": "채널A",
    "tvchosun": "TV조선", "sportschosun": "스포츠조선",
    "sportsdonga": "스포츠동아", "heraldcorp": "헤럴드경제",
    "bizwatch": "비즈워치", "thebell": "더벨", "dealsite": "딜사이트",
    "biz": "비즈니스포스트", "naver": "네이버뉴스",
    "theqoo": "더쿠", "instiz": "인스티즈",
}


def extract_outlet(originallink: str, link: str) -> str:
    """URL에서 매체명 추출"""
    url = originallink or link
    try:
        netloc = urlparse(url).netloc.lower()
        netloc = netloc.replace("www.", "").replace("m.", "").replace("n.", "")
        domain_key = netloc.split(".")[0]
        return DOMAIN_MAP.get(domain_key, netloc.split(".")[0])
    except Exception:
        return ""

load_dotenv(Path(__file__).parent.parent / ".env")

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


# ─────────────────────────────────────────────
# 섹션① 유통 주요기사 REVIEW 키워드
# ─────────────────────────────────────────────
SECTION1_KEYWORDS = {
    "정부정책_규제": [
        "유통산업발전법", "대형마트 의무휴업", "복합쇼핑몰 규제",
        "유통 공정거래", "중대재해 유통", "유통 출점 규제",
    ],
    "마케팅_IT트렌드": [
        "백화점 팝업스토어", "체험형 매장", "라이브커머스 유통",
        "리테일 AI", "백화점 MZ 마케팅", "유통 O2O",
    ],
    "ESG_상생": [
        "유통 ESG", "백화점 친환경", "유통 동반성장",
        "중소기업 상생 유통", "유통 사회공헌",
    ],
    "조직문화_노동": [
        "유통 감정노동", "유통 워라밸", "백화점 직원 복지",
        "유통업계 MZ세대", "유통 채용",
    ],
}

# ─────────────────────────────────────────────
# 섹션② 사건사고 / 반면교사 키워드
# ─────────────────────────────────────────────
SECTION2_KEYWORDS = {
    "갑질_윤리논란": [
        "롯데백화점 갑질", "이마트 갑질", "신세계 갑질",
        "홈플러스 논란", "유통 갑질 논란", "백화점 협력사 갑질",
    ],
    "안전_위생사고": [
        "백화점 안전사고", "유통 식품 위생불량", "마트 화재",
        "유통 식품 회수", "백화점 시설 사고",
    ],
    "개인정보_보안": [
        "유통 개인정보 유출", "마트 해킹", "유통 보안사고",
    ],
    "허위광고_소비자피해": [
        "유통 허위광고", "마트 과장광고", "유통 소비자 피해",
        "유통 환불 거부",
        "온라인 가품", "쇼핑 가품", "가품 논란",
        "소비자 기만", "유통 기만",
    ],
    "성차별_사회논란": [
        "유통 성차별 논란", "백화점 SNS 논란", "유통 비하 논란",
    ],
}

# ─────────────────────────────────────────────
# 섹션④ 경쟁사 일반 동향 키워드
# ─────────────────────────────────────────────
SECTION4_KEYWORDS = [
    "롯데백화점 동향", "롯데백화점 전략", "롯데백화점 신규",
    "신세계백화점 동향", "신세계마켓", "신세계 전략",
    "이마트 동향", "이마트 신사업",
    "쿠팡 동향", "쿠팡 전략", "쿠팡 신규",
    "무신사 동향", "무신사 전략",
    "홈플러스 동향", "GS리테일 동향",
    "올리브영 동향", "올리브영 전략",
]

# ─────────────────────────────────────────────
# 섹션③ 당사 관련기사 REVIEW 키워드
# ─────────────────────────────────────────────
SECTION3_KEYWORDS = [
    "현대백화점그룹", "현대지에프홀딩스",
    "현대백화점", "현대프리미엄아울렛", "현대아울렛", "현대면세점",
    "현대홈쇼핑",
    "현대그린푸드", "현대그린푸드 급식", "현대그린푸드 실적",
    "현대바이오랜드",
    "한섬",
    "현대리바트", "지누스", "현대L&C",
    "현대퓨처넷", "현대에버다임", "현대이지웰", "현대벤디스",
]


def search_news(keyword: str, display: int = 20, start: int = 1) -> list:
    enc_keyword = urllib.parse.quote(keyword)
    url = (
        f"https://openapi.naver.com/v1/search/news.json"
        f"?query={enc_keyword}&display={display}&start={start}&sort=date"
    )
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

    try:
        response = urllib.request.urlopen(request)
        result = json.loads(response.read().decode("utf-8"))
        return result.get("items", [])
    except Exception as e:
        print(f"[크롤러 오류] {keyword}: {e}")
        return []


def search_news_paginated(keyword: str, display: int = 100, days_back: int = 7) -> list:
    """
    페이지네이션으로 days_back일치 기사를 수집.
    Naver API start=1~1000, display<=100 제한 내에서 동작.
    충분한 과거 기사가 나오면 조기 종료.
    """
    all_items = []
    seen_links = set()

    for start in range(1, 1001, display):
        items = search_news(keyword, display=display, start=start)
        if not items:
            break

        new_items = []
        oldest_in_batch = None

        for item in items:
            link = item.get("link", "")
            if link in seen_links:
                continue
            seen_links.add(link)

            pub_date = item.get("pubDate", "")
            if pub_date:
                if not is_within_days(pub_date, days_back):
                    # 이 배치의 가장 오래된 기사가 범위 밖 → 더 이상 페이지 불필요
                    oldest_in_batch = pub_date
                    break
            new_items.append(item)

        all_items.extend(new_items)

        # 마지막 기사가 범위 밖이면 종료
        if oldest_in_batch is not None:
            break

        # 한 페이지가 가득 차지 않으면 더 없음
        if len(items) < display:
            break

    return all_items


def clean_html(text: str) -> str:
    return (
        text.replace("<b>", "").replace("</b>", "")
            .replace("&quot;", '"').replace("&amp;", "&")
            .replace("&#39;", "'")
    )


def is_within_days(pub_date_str: str, days_back: int) -> bool:
    """발행일이 days_back일 이내인지 확인"""
    try:
        pub_dt = parsedate_to_datetime(pub_date_str)
        now = datetime.now(timezone.utc)
        return (now - pub_dt) <= timedelta(days=days_back)
    except Exception:
        return True  # 파싱 실패 시 통과


def parse_pub_date_kst(pub_date_str: str) -> str:
    """RFC 2822 pub_date → 'YYYY-MM-DD' (KST 기준)"""
    KST = timezone(timedelta(hours=9))
    try:
        dt = parsedate_to_datetime(pub_date_str)
        return dt.astimezone(KST).strftime("%Y-%m-%d")
    except Exception:
        from datetime import date
        return date.today().isoformat()


def collect_all_articles(days_back: int = 7, max_display: int = 20, paginate: bool = False) -> list:
    """
    days_back:   이 일수 이내 기사만 수집
    max_display: 일반 수집 시 키워드당 최대 수집 수
    paginate:    True면 페이지네이션으로 days_back 전체 기간 탐색 (초기 수집용)
    """
    all_articles = []
    seen_links = set()

    def add_articles(items: list, report_section: str, hint_category: str, keyword: str):
        for item in items:
            pub_date = item.get("pubDate", "")
            if pub_date and not is_within_days(pub_date, days_back):
                continue
            link = item.get("link", "")
            originallink = item.get("originallink", "")
            if link in seen_links:
                continue
            seen_links.add(link)
            all_articles.append({
                "title": clean_html(item.get("title", "")),
                "link": link,
                "outlet": extract_outlet(originallink, link),
                "description": clean_html(item.get("description", "")),
                "pub_date": pub_date,
                "search_keyword": keyword,
                "report_section": report_section,
                "hint_category": hint_category,
            })

    def fetch(kw, display):
        if paginate:
            return search_news_paginated(kw, display=100, days_back=days_back)
        return search_news(kw, display=display)

    # 섹션① 유통 주요기사
    print(f"[크롤러] 섹션① 유통 주요기사 수집 중...")
    for category, keywords in SECTION1_KEYWORDS.items():
        for kw in keywords:
            add_articles(fetch(kw, min(max_display, 10)),
                         report_section="섹션1_유통트렌드", hint_category=category, keyword=kw)

    # 섹션② 반면교사
    print(f"[크롤러] 섹션② 반면교사 수집 중...")
    for category, keywords in SECTION2_KEYWORDS.items():
        for kw in keywords:
            add_articles(fetch(kw, min(max_display, 8)),
                         report_section="섹션2_반면교사", hint_category=category, keyword=kw)

    # 섹션③ 당사 관련
    print(f"[크롤러] 섹션③ 당사 관련기사 수집 중...")
    for kw in SECTION3_KEYWORDS:
        add_articles(fetch(kw, max_display),
                     report_section="섹션3_당사관련", hint_category="당사관련", keyword=kw)

    # 섹션④ 경쟁사 일반 동향
    print(f"[크롤러] 섹션④ 경쟁사 동향 수집 중...")
    for kw in SECTION4_KEYWORDS:
        add_articles(fetch(kw, min(max_display, 10)),
                     report_section="섹션4_경쟁사관련", hint_category="경쟁사동향", keyword=kw)

    print(f"[크롤러] 총 {len(all_articles)}개 기사 수집 완료")
    return all_articles
