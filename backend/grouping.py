"""
기사 유사도 기반 그룹핑 (KoNLPy 없이 동작)

알고리즘:
  - 제목을 공백 기준 토큰화 후 한국어 단어(2자 이상) 추출
  - 기사 쌍(pair)별 Jaccard 유사도 계산
  - 유사도 ≥ 0.5인 기사들을 Union-Find로 같은 그룹에 묶음
  - 그룹 내 기사가 2건 이상일 때만 group_id 부여
"""
import re
from collections import defaultdict

STOPWORDS = {
    '및', '의', '이', '가', '을', '를', '은', '는', '에', '에서',
    '로', '으로', '와', '과', '도', '뉴스', '기자', '=', '기사',
    '속보', '단독', '종합', '업데이트', '수정', '오전', '오후',
    '합니다', '했습니다', '입니다', '이다', '하는', '하며',
}

# 약어 → 정식명 정규화 (유사도 계산 전 치환)
NORMALIZE = {
    '현대百': '현대백화점',
    '롯데百': '롯데백화점',
    '신세계百': '신세계백화점',
    '갤러리아百': '갤러리아백화점',
    'AK百': 'AK플라자',
    '현대百화점': '현대백화점',   # 혼합 표기 방어
}


def normalize(title: str) -> str:
    """약어를 정식명으로 치환"""
    for abbr, full in NORMALIZE.items():
        title = title.replace(abbr, full)
    return title


def extract_words(title: str) -> set:
    """제목에서 의미 있는 단어 추출 (2자 이상 한국어/영문/숫자 단어)"""
    text = re.sub(r'[^\w\s가-힣a-zA-Z0-9]', ' ', normalize(title))
    words = set()
    for w in text.split():
        w = w.strip()
        if len(w) >= 2 and w not in STOPWORDS:
            words.add(w)
    return words


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    union = len(a | b)
    return len(a & b) / union if union > 0 else 0.0


def compute_group_ids(articles: list[dict]) -> list[str | None]:
    """
    articles: [{"title": str, ...}, ...]
    반환: 각 기사의 group_id 리스트 (단독 기사는 None)
    """
    n = len(articles)
    if n == 0:
        return []

    word_sets = [extract_words(a["title"]) for a in articles]

    # Union-Find
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            if jaccard(word_sets[i], word_sets[j]) >= 0.35:
                union(i, j)

    # 같은 그룹 멤버 수집
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    # group_id 할당 (2건 이상만)
    result: list[str | None] = [None] * n
    gid_counter = 0
    for leader in sorted(groups):
        members = groups[leader]
        if len(members) >= 2:
            gid = f"g{gid_counter:04d}"
            gid_counter += 1
            for idx in members:
                result[idx] = gid

    return result
