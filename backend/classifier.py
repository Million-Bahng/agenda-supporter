"""
키워드 룰 기반 기사 분류 (Claude API 없이 동작)

분류 우선순위:
1. 당사 계열사 직접 언급 → 섹션3
2. 특정 기업명 + 위기 키워드 → 섹션2 반면교사
3. 유통 트렌드/정책 키워드 → 섹션1
4. 그 외 → 기타

핵심 원칙:
- 반면교사는 반드시 구체적 기업명(당사 또는 경쟁사)이 있어야 함
- 일반 사건사고/일정/오피니언은 기타로 분류
"""

# ─────────────────────────────────────────────
# 기업 키워드
# ─────────────────────────────────────────────

COMPANY_KEYWORDS = [
    "현대지에프홀딩스", "현대백화점그룹",
    "현대백화점", "현대홈쇼핑", "현대아울렛", "현대프리미엄아울렛",
    "현대백", "현대百", "현대면세점",
    "현대리바트", "리바트", "지누스",
    "현대L&C", "한섬",
    "현대그린푸드", "현대바이오랜드",
    "현대퓨처넷", "현대에버다임", "현대이지웰", "현대벤디스",
]

COMPETITOR_KEYWORDS = [
    "롯데백화점", "롯데百", "롯데마트", "롯데쇼핑", "롯데홈쇼핑", "롯데온",
    "신세계백화점", "신세계百", "신세계", "이마트", "SSG닷컴",
    "갤러리아백화점", "갤러리아百", "AK플라자", "AK百",
    "GS리테일", "GS홈쇼핑", "GS25", "GS샵",
    "CJ온스타일", "CJ올리브영", "올리브영",
    "홈플러스", "쿠팡", "무신사",
    "위메프", "11번가", "G마켓", "옥션", "티몬",
]

ALL_COMPANIES = COMPANY_KEYWORDS + COMPETITOR_KEYWORDS

# ─────────────────────────────────────────────
# 업계 그룹: 동일 업계 2개사 이상 등장 시 섹션1 분류
# ─────────────────────────────────────────────
INDUSTRY_GROUPS = [
    # (그룹명, 카테고리, 키워드 리스트, 최소 매칭 수)
    ("백화점", "마케팅_IT트렌드", [
        "롯데백화점", "롯데百", "신세계백화점", "신세계百",
        "현대백화점", "현대百", "갤러리아백화점", "갤러리아百",
        "AK플라자", "AK百",
    ], 2),
    ("홈쇼핑", "마케팅_IT트렌드", [
        "현대홈쇼핑", "CJ온스타일", "롯데홈쇼핑", "GS샵", "GS홈쇼핑",
    ], 2),
    ("대형마트", "마케팅_IT트렌드", [
        "이마트", "롯데마트", "홈플러스", "코스트코",
    ], 2),
    ("단체급식", "마케팅_IT트렌드", [
        "현대그린푸드", "삼성웰스토리", "아워홈", "CJ프레시웨이", "푸디스트",
    ], 2),
    ("이커머스", "마케팅_IT트렌드", [
        "쿠팡", "SSG닷컴", "11번가", "G마켓", "네이버쇼핑",
        "위메프", "티몬", "무신사",
    ], 2),
    ("유통", "마케팅_IT트렌드", [
        "롯데", "현대", "신세계",
    ], 2),
    ("가구", "마케팅_IT트렌드", [
        "현대리바트", "한샘", "신세계까사", "퍼시스", "에넥스",
    ], 2),
    ("패션", "마케팅_IT트렌드", [
        "한섬", "삼성물산", "LF", "에프앤에프", "영원무역",
    ], 2),
]

# 섹션2 반면교사: 기업명과 함께 나와야 의미 있는 위기 키워드
CRISIS_KEYWORDS = [
    # 윤리/갑질
    "갑질", "불공정거래", "허위광고", "과대광고", "담합",
    "과징금", "횡령", "배임", "탈세", "리베이트",
    "납품단가", "공정위 제재", "공정위 조사", "소비자 기만",
    # 안전/위생 (기업 책임 맥락)
    "식중독", "이물질", "위생불량", "제품결함", "유해물질",
    "리콜", "불량제품", "안전사고", "부상자 발생",
    # 개인정보
    "개인정보 유출", "해킹 피해", "정보유출", "고객정보 유출",
    # 사회논란
    "논란", "불매", "사과문 발표", "직장내괴롭힘", "갑을 논란",
    # 소비자 신뢰 (가품/위조/품질)
    "가품", "위조품", "짝퉁", "가품 판정", "정품 위조", "품질 논란",
    "소비자 피해", "환불 거부", "배송 지연 논란", "구매 피해",
]

# 섹션1 트렌드/정책 키워드
SECTION1_RULES = [
    ("정부정책_규제", [
        "출점규제", "의무휴업", "대규모점포", "공정거래법 개정",
        "중대재해처벌법", "유통산업발전법", "산업통상자원부",
        "최저임금 인상", "주52시간", "규제 완화", "규제 강화",
    ], 6),
    ("마케팅_IT트렌드", [
        "팝업스토어", "팝업", "라이브커머스", "라이브방송 쇼핑",
        "AI 쇼핑", "옴니채널", "디지털전환", "리테일테크",
        "퀵커머스", "새벽배송", "콘텐츠커머스", "숏폼 커머스",
        "구독서비스", "버티컬커머스", "리셀", "명품 플랫폼",
    ], 5),
    ("ESG_상생", [
        "ESG 경영", "탄소중립", "친환경 포장", "재활용 포장",
        "동반성장", "상생 협력", "지속가능경영", "사회공헌",
        "RE100", "친환경 매장",
    ], 5),
    ("조직문화_노동", [
        "감정노동 보호", "워라밸", "MZ세대 직원",
        "직원 복지", "육아휴직 확대", "재택근무 도입",
        "유연근무제", "번아웃", "이직률 감소",
    ], 4),
]

# 제목 패턴으로 걸러낼 무관 기사
EXCLUDE_TITLE_PATTERNS = [
    "오늘의 일정", "주요 일정", "주요일정", "경제 일정",
    "산업 일정", "오늘의 날씨", "소방청 상황",
    "사건사고", "주요 사건", "브리핑" ,"오늘의 증시",
    "코스피", "코스닥", "환율", "금리",
]


# ─────────────────────────────────────────────
# 분류 함수
# ─────────────────────────────────────────────

def _hits(text: str, keywords: list) -> int:
    return sum(1 for kw in keywords if kw in text)


def _find_company(text: str, companies: list) -> str | None:
    return next((kw for kw in companies if kw in text), None)


def classify_article(title: str, description: str, hint_category: str = "") -> dict:
    text = title + " " + description

    # ── 무관 기사 조기 제외 ──
    for pattern in EXCLUDE_TITLE_PATTERNS:
        if pattern in title:
            return _etc()

    # ── 섹션3: 당사 계열사 — 제목에 기업명 있어야 함 ──
    company = _find_company(title, COMPANY_KEYWORDS)
    if company:
        score = 8.0 if any(kw in text for kw in CRISIS_KEYWORDS) else 6.0
        return {
            "category": "당사관련",
            "report_section": "섹션3_당사관련",
            "relevance_score": score,
            "importance": "상" if score >= 8 else "중",
            "is_competitor": False,
            "related_company": company,
            "ai_memo": f"[당사관련] {title[:45]} → 언론 모니터링 필요",
        }

    # ── 섹션2: 경쟁사 — 제목에 기업명 + 위기 키워드 있어야 함 ──
    # ── 섹션4: 경쟁사 — 위기 키워드 없는 일반 경쟁사 기사 ──
    competitor = _find_company(title, COMPETITOR_KEYWORDS)
    if competitor:
        crisis_hits = _hits(text, CRISIS_KEYWORDS)
        if crisis_hits > 0:
            score = min(7 + crisis_hits, 10)
            category = _pick_crisis_category(text)
            return {
                "category": category,
                "report_section": "섹션2_반면교사",
                "relevance_score": float(score),
                "importance": "상" if score >= 8 else "중",
                "is_competitor": True,
                "related_company": competitor,
                "ai_memo": f"[{category}] {title[:45]} → 당사 유사 리스크 점검 필요",
            }
        else:
            return {
                "category": "경쟁사관련",
                "report_section": "섹션4_경쟁사관련",
                "relevance_score": 5.0,
                "importance": "하",
                "is_competitor": False,
                "related_company": competitor,
                "ai_memo": f"[경쟁사동향] {title[:45]} → 경쟁사 동향 참고",
            }

    # ── 섹션1: 업계 트렌드 (동일 업계 복수 기업 등장) ──
    for group_name, category, keywords, min_count in INDUSTRY_GROUPS:
        matched = [kw for kw in keywords if kw in text]
        if len(matched) >= min_count:
            return {
                "category": category,
                "report_section": "섹션1_유통트렌드",
                "relevance_score": 6.0,
                "importance": "중",
                "is_competitor": False,
                "related_company": "해당없음",
                "ai_memo": f"[{group_name} 트렌드] {title[:45]} → 업계 동향 모니터링 필요",
            }

    # ── 섹션1: 유통 트렌드/정책 ──
    for category, keywords, base_score in SECTION1_RULES:
        h = _hits(text, keywords)
        if h == 0:
            continue
        score = min(base_score + h - 1, 9)
        return {
            "category": category,
            "report_section": "섹션1_유통트렌드",
            "relevance_score": float(score),
            "importance": "상" if score >= 8 else "중" if score >= 5 else "하",
            "is_competitor": False,
            "related_company": "해당없음",
            "ai_memo": f"[{category}] {title[:45]} → 트렌드 모니터링 필요",
        }

    return _etc()


def _pick_crisis_category(text: str) -> str:
    if any(kw in text for kw in ["개인정보 유출", "해킹", "정보유출", "고객정보 유출"]):
        return "반면교사_개인정보"
    if any(kw in text for kw in ["식중독", "이물질", "위생불량", "유해물질", "리콜", "안전사고"]):
        return "반면교사_안전위생"
    if any(kw in text for kw in ["가품", "위조품", "짝퉁", "가품 판정", "소비자 피해", "환불 거부", "품질 논란"]):
        return "반면교사_소비자신뢰"
    if any(kw in text for kw in ["논란", "불매", "사과문", "직장내괴롭힘", "갑을 논란"]):
        return "반면교사_사회논란"
    return "반면교사_갑질윤리"


def _etc() -> dict:
    return {
        "category": "기타",
        "report_section": "",
        "relevance_score": 0.0,
        "importance": "하",
        "is_competitor": False,
        "related_company": "해당없음",
        "ai_memo": "",
    }


def classify_articles_batch(articles: list) -> list:
    results = []
    total = len(articles)
    for i, article in enumerate(articles, 1):
        if i % 50 == 0:
            print(f"[분류] {i}/{total}건 처리 중...")
        classification = classify_article(
            article["title"],
            article.get("description", ""),
            article.get("hint_category", ""),
        )
        results.append({**article, **classification})
    print(f"[분류 완료] 총 {total}건")
    return results
