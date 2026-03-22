"""
경전회의 기사 대시보드 - FastAPI 메인 앱
"""
import threading
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, BackgroundTasks, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models import Article, SavedArticle, SessionLocal, get_db, init_db
from pipeline import run_crawl_and_classify
from scheduler import start_scheduler, stop_scheduler

app = FastAPI(title="경전회의 기사 대시보드", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()

    # DB가 비어있으면 초기 30일 수집 자동 실행
    db = SessionLocal()
    try:
        count = db.query(Article).count()
    finally:
        db.close()

    if count == 0:
        print("[시작] DB가 비어있습니다. 초기 30일 수집을 백그라운드에서 시작합니다...")

        def initial_collect():
            db2 = SessionLocal()
            try:
                run_crawl_and_classify(db2, mode="initial")
            finally:
                db2.close()

        thread = threading.Thread(target=initial_collect, daemon=True)
        thread.start()

    start_scheduler()


@app.on_event("shutdown")
def shutdown():
    stop_scheduler()


# ─────────────────────────────────────────────
# 날짜 목록 API
# ─────────────────────────────────────────────

@app.get("/dates", summary="기사가 있는 날짜 목록")
def get_dates(db: Session = Depends(get_db)):
    """수집된 날짜 목록을 내림차순으로 반환 (수동 진행 포함)"""
    rows = (
        db.query(Article.collected_date, func.count(Article.id))
        .filter(Article.report_section != "")
        .filter(Article.collected_date != "수동 진행")
        .group_by(Article.collected_date)
        .order_by(desc(Article.collected_date))
        .all()
    )
    return [{"date": date_str, "count": count} for date_str, count in rows]


# ─────────────────────────────────────────────
# 크롤링 실행
# ─────────────────────────────────────────────

@app.post("/crawl", summary="수동 크롤링 실행")
def trigger_crawl(background_tasks: BackgroundTasks):
    """사용자가 직접 실행하는 수동 수집 (collected_date = '수동 진행')"""
    def do_manual():
        db = SessionLocal()
        try:
            run_crawl_and_classify(db, mode="manual")
        finally:
            db.close()

    background_tasks.add_task(do_manual)
    return {"message": "수동 수집을 백그라운드에서 시작했습니다."}


# ─────────────────────────────────────────────
# 기사 조회 API
# ─────────────────────────────────────────────

@app.get("/articles", summary="기사 목록 조회")
def get_articles(
    date: Optional[str] = Query(None, description="수집일 YYYY-MM-DD 또는 '수동 진행'"),
    section: Optional[str] = Query(None, description="섹션1_유통트렌드 등"),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Article).filter(Article.report_section != "")

    if date:
        q = q.filter(Article.collected_date == date)
    if section:
        q = q.filter(Article.report_section == section)

    articles = q.order_by(desc(Article.created_at)).limit(limit).all()
    return [_article_to_dict(a) for a in articles]


@app.get("/articles/{article_id}", summary="기사 상세")
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
    return _article_to_dict(article)


# ─────────────────────────────────────────────
# 통계 API
# ─────────────────────────────────────────────

@app.get("/stats", summary="대시보드 통계")
def get_stats(
    date: Optional[str] = Query(None, description="수집일 YYYY-MM-DD 또는 '수동 진행'"),
    db: Session = Depends(get_db),
):
    base_q = db.query(Article).filter(Article.report_section != "")
    if date:
        base_q = base_q.filter(Article.collected_date == date)

    total = base_q.count()

    section_counts = {}
    for section in ["섹션1_유통트렌드", "섹션2_반면교사", "섹션3_당사관련", "섹션4_경쟁사관련"]:
        section_counts[section] = base_q.filter(Article.report_section == section).count()

    return {
        "total": total,
        "by_section": section_counts,
        "competitor_cases": section_counts.get("섹션2_반면교사", 0),
    }


# ─────────────────────────────────────────────
# 저장 기사 API
# ─────────────────────────────────────────────

@app.post("/saved/{article_id}", summary="기사 저장")
def save_article(article_id: int, db: Session = Depends(get_db)):
    # 이미 저장된 경우
    if db.query(SavedArticle).filter(SavedArticle.article_id == article_id).first():
        return {"message": "이미 저장된 기사입니다."}

    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")

    saved = SavedArticle(
        article_id=article.id,
        title=article.title,
        link=article.link,
        outlet=article.outlet or "",
        description=article.description or "",
        pub_date=article.pub_date or "",
        collected_date=article.collected_date or "",
        report_section=article.report_section or "",
        category=article.category or "",
        related_company=article.related_company or "",
        ai_memo=article.ai_memo or "",
        is_competitor=article.is_competitor or False,
    )
    db.add(saved)
    db.commit()
    return {"message": "기사가 저장되었습니다."}


@app.get("/saved", summary="저장된 기사 목록")
def get_saved(db: Session = Depends(get_db)):
    rows = db.query(SavedArticle).order_by(desc(SavedArticle.saved_at)).all()
    return [_saved_to_dict(s) for s in rows]


@app.get("/saved/ids", summary="저장된 기사 ID 목록")
def get_saved_ids(db: Session = Depends(get_db)):
    rows = db.query(SavedArticle.article_id).all()
    return [r[0] for r in rows]


@app.delete("/saved", summary="저장 기사 전체 비우기")
def clear_saved(db: Session = Depends(get_db)):
    deleted = db.query(SavedArticle).delete()
    db.commit()
    return {"message": f"저장 기사 {deleted}건이 삭제되었습니다."}


@app.delete("/saved/{article_id}", summary="저장 기사 개별 삭제")
def delete_saved(article_id: int, db: Session = Depends(get_db)):
    row = db.query(SavedArticle).filter(SavedArticle.article_id == article_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="저장된 기사를 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"message": "삭제되었습니다."}


# ─────────────────────────────────────────────
# 관리 API
# ─────────────────────────────────────────────

@app.post("/admin/cleanup-unclassified", summary="기타(미분류) 기사 DB 정리")
def cleanup_unclassified(db: Session = Depends(get_db)):
    deleted = db.query(Article).filter(Article.report_section == "").delete()
    db.commit()
    return {"message": f"미분류 기사 {deleted}건 삭제 완료"}


# ─────────────────────────────────────────────
# 직렬화 헬퍼
# ─────────────────────────────────────────────

def _article_to_dict(a: Article) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "link": a.link,
        "outlet": a.outlet or "",
        "description": a.description,
        "pub_date": a.pub_date,
        "collected_date": a.collected_date,
        "report_section": a.report_section,
        "category": a.category,
        "relevance_score": a.relevance_score,
        "importance": a.importance,
        "related_company": a.related_company,
        "is_competitor": a.is_competitor,
        "ai_memo": a.ai_memo,
        "group_id": a.group_id,
    }


def _saved_to_dict(s: SavedArticle) -> dict:
    return {
        "id": s.id,
        "article_id": s.article_id,
        "title": s.title,
        "link": s.link,
        "outlet": s.outlet or "",
        "description": s.description,
        "pub_date": s.pub_date,
        "collected_date": s.collected_date,
        "report_section": s.report_section,
        "category": s.category,
        "related_company": s.related_company,
        "is_competitor": s.is_competitor,
        "ai_memo": s.ai_memo,
        "saved_at": s.saved_at.isoformat() if s.saved_at else None,
    }
