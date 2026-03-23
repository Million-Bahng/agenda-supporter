from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, datetime, timedelta, timezone
from models import SessionLocal, Article

scheduler = BackgroundScheduler(timezone="Asia/Seoul")


def scheduled_job():
    from pipeline import run_crawl_and_classify
    db = SessionLocal()
    try:
        run_crawl_and_classify(db, mode="auto")

        cutoff = (date.today() - timedelta(days=30)).isoformat()
        deleted = db.query(Article).filter(
            Article.collected_date < cutoff,
            Article.collected_date != "수동 진행",
        ).delete()
        db.commit()
        if deleted:
            print(f"[스케줄러] 만료 기사 {deleted}건 삭제 (기준: {cutoff})")
    finally:
        db.close()


def _is_today_collected() -> bool:
    """오늘 날짜로 수집된 기사가 이미 있는지 확인"""
    today = date.today().isoformat()
    db = SessionLocal()
    try:
        count = db.query(Article).filter(
            Article.collected_date == today,
            Article.report_section != "",
        ).count()
        return count > 0
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        scheduled_job,
        trigger=CronTrigger(hour=9, minute=0),
        id="daily_crawl",
        replace_existing=True,
    )
    scheduler.start()
    print("[스케줄러] 매일 오전 09:00 자동 크롤링 등록 완료")

    # ✅ 핵심 보정: 9시 이후 시작된 경우 오늘 수집이 누락됐으면 즉시 실행
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    if now_kst.hour >= 9 and not _is_today_collected():
        print("[스케줄러] 오늘 수집 누락 감지 → 즉시 수집 시작")
        scheduler.add_job(scheduled_job, id="catchup_crawl", replace_existing=True)


def stop_scheduler():
    scheduler.shutdown()
