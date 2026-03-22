"""
크롤링 + 분류 + DB 저장 파이프라인

모드:
  "initial" — 서버 시작 시 DB 비어있을 때. 최근 30일치 수집, pub_date → collected_date
  "auto"    — 매일 09:00 스케줄러. 수동 진행 삭제 후 당일 기사 수집, collected_date = 오늘
  "manual"  — 사용자 버튼 클릭. 기존 수동 진행 삭제 후 수집, collected_date = "수동 진행"
"""
from datetime import date
from sqlalchemy.orm import Session

from models import Article
from crawler import collect_all_articles, parse_pub_date_kst
from classifier import classify_articles_batch
from grouping import compute_group_ids


def _delete_manual_entries(db: Session):
    """수동 진행 레코드 전체 삭제"""
    deleted = db.query(Article).filter(Article.collected_date == "수동 진행").delete()
    db.commit()
    if deleted:
        print(f"[파이프라인] 수동 진행 레코드 {deleted}건 삭제")


def _save_articles(db: Session, classified: list, collected_date: str):
    """분류된 기사를 DB에 저장 (기타·중복 제외). 저장 건수 반환."""
    saved = skipped_etc = skipped_dup = 0

    for a in classified:
        if not a.get("report_section"):
            skipped_etc += 1
            continue

        # 중복 확인: 같은 링크 + 유효 섹션
        if db.query(Article).filter(
            Article.link == a["link"],
            Article.report_section != "",
        ).first():
            skipped_dup += 1
            continue

        article = Article(
            title=a["title"],
            link=a["link"],
            outlet=a.get("outlet", ""),
            description=a.get("description", ""),
            pub_date=a.get("pub_date", ""),
            search_keyword=a.get("search_keyword", ""),
            report_section=a.get("report_section", ""),
            hint_category=a.get("hint_category", ""),
            category=a.get("category", "기타"),
            relevance_score=a.get("relevance_score", 0),
            importance=a.get("importance", "하"),
            related_company=a.get("related_company", "해당없음"),
            ai_memo=a.get("ai_memo", ""),
            is_competitor=a.get("is_competitor", False),
            collected_date=collected_date,
        )
        db.add(article)
        saved += 1

    db.commit()
    print(f"[파이프라인] 저장 {saved}건 / 기타제외 {skipped_etc}건 / 중복제외 {skipped_dup}건")
    return saved


def _run_grouping(db: Session, collected_date: str):
    """특정 날짜의 기사 그룹핑 실행 후 group_id 업데이트"""
    articles = db.query(Article).filter(
        Article.collected_date == collected_date,
        Article.report_section != "",
    ).all()

    if not articles:
        return

    article_dicts = [{"title": a.title} for a in articles]
    group_ids = compute_group_ids(article_dicts)

    for article, gid in zip(articles, group_ids):
        article.group_id = gid
    db.commit()

    grouped = sum(1 for g in group_ids if g is not None)
    print(f"[그룹핑] {collected_date} - {grouped}건 그룹 할당 완료")


def run_crawl_and_classify(db: Session, mode: str = "auto"):
    """
    mode:
      "initial" — 최근 30일치 수집, pub_date를 collected_date로 사용
      "auto"    — 수동 진행 삭제 후 당일 기사 수집
      "manual"  — 기존 수동 진행 삭제 후 재수집, collected_date = "수동 진행"
    """
    today = date.today().isoformat()
    print(f"[파이프라인] mode={mode} 크롤링 시작 ({today})")

    if mode == "initial":
        raw_articles = collect_all_articles(days_back=14, max_display=100, paginate=True)
        classified = classify_articles_batch(raw_articles)

        # pub_date 기준으로 날짜별 분리 저장
        from collections import defaultdict
        by_date: dict[str, list] = defaultdict(list)
        for a in classified:
            if a.get("report_section"):
                collected = parse_pub_date_kst(a.get("pub_date", "")) if a.get("pub_date") else today
                a["_collected_date"] = collected
                by_date[collected].append(a)

        total_saved = 0
        for collected_date, articles in by_date.items():
            saved = _save_articles(db, articles, collected_date)
            total_saved += saved
            if saved > 0:
                _run_grouping(db, collected_date)

        print(f"[파이프라인] 초기 수집 완료 - 총 {total_saved}건 / {len(by_date)}개 날짜")

    elif mode == "auto":
        _delete_manual_entries(db)
        raw_articles = collect_all_articles(days_back=7, max_display=20)
        classified = classify_articles_batch(raw_articles)
        saved = _save_articles(db, classified, today)
        if saved > 0:
            _run_grouping(db, today)

    elif mode == "manual":
        _delete_manual_entries(db)
        raw_articles = collect_all_articles(days_back=1, max_display=20)
        classified = classify_articles_batch(raw_articles)
        saved = _save_articles(db, classified, "수동 진행")
        if saved > 0:
            _run_grouping(db, "수동 진행")
    else:
        raise ValueError(f"알 수 없는 mode: {mode}")
