"""
APScheduler 기반 자동 크롤링 스케줄러
매일 09:00에 크롤링 + 분류 실행
  - 수동 진행 레코드 삭제
  - 전날 09:00 ~ 당일 09:00 기사 수집
  - 30일 지난 기사 자동 삭제
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, timedelta
from models import SessionLocal, Article

scheduler = BackgroundScheduler(timezone="Asia/Seoul")


def scheduled_job():
    from pipeline import run_crawl_and_classify
    db = SessionLocal()
    try:
        # auto 크롤링 실행 (수동 진행 삭제 포함)
        run_crawl_and_classify(db, mode="auto")

        # 30일 이상 지난 기사 자동 삭제
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


def start_scheduler():
    scheduler.add_job(
        scheduled_job,
        trigger=CronTrigger(hour=9, minute=0),
        id="daily_crawl",
        replace_existing=True,
    )
    scheduler.start()
    print("[스케줄러] 매일 오전 09:00 자동 크롤링 등록 완료")


def stop_scheduler():
    scheduler.shutdown()
