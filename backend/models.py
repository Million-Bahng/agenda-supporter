from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agenda.db")

# SQLite: check_same_thread=False 필요 / PostgreSQL: 불필요
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False)
    outlet = Column(String(100))               # 매체명
    description = Column(Text)
    pub_date = Column(String(100))
    search_keyword = Column(String(100))       # 검색에 사용된 키워드
    report_section = Column(String(20))        # 섹션1_유통트렌드 / 섹션2_반면교사 / 섹션3_당사관련 / 섹션4_경쟁사관련
    hint_category = Column(String(50))         # 크롤러 단계 힌트 카테고리

    # 분류 결과
    category = Column(String(50))              # 최종 분류 카테고리
    relevance_score = Column(Float, default=0)
    importance = Column(String(10))            # 상/중/하 (레거시, 향후 제거 예정)
    related_company = Column(String(100))      # 관련 기업명
    ai_memo = Column(Text)                     # 회의자료용 메모
    is_competitor = Column(Boolean, default=False)

    group_id = Column(String(50))              # 유사 기사 그룹 ID (nullable)

    created_at = Column(DateTime, default=datetime.utcnow)
    collected_date = Column(String(20))        # YYYY-MM-DD 또는 "수동 진행"


class SavedArticle(Base):
    """경전회의 자료용으로 별도 보관하는 기사 (날짜 무관 영구 보관)"""
    __tablename__ = "saved_articles"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False, unique=True)  # 원본 Article.id
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False)
    outlet = Column(String(100))
    description = Column(Text)
    pub_date = Column(String(100))
    collected_date = Column(String(20))
    report_section = Column(String(20))
    category = Column(String(50))
    related_company = Column(String(100))
    ai_memo = Column(Text)
    is_competitor = Column(Boolean, default=False)
    saved_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
