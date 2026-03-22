# 경전회의 기사 대시보드 — 인수인계 문서

> 마지막 업데이트: 2026-03-22

---

## 프로젝트 개요

현대백화점그룹 홍보실 **경전회의** 준비 자동화 도구.
매일 아침 9시에 네이버 뉴스를 자동 수집·분류하여 회의자료용 기사 대시보드를 제공한다.

---

## 배포 현황

| 구분 | 플랫폼 | URL |
|------|--------|-----|
| 백엔드 (FastAPI) | Railway | `https://agenda-supporter-production.up.railway.app` |
| 프론트엔드 (Next.js) | Vercel | (Vercel 대시보드에서 확인) |
| DB | Railway PostgreSQL | `caboose.proxy.rlwy.net:55030` (public) |

### Railway 설정 주의사항
- **Serverless 모드 OFF** 필수 (Settings → Sleep 옵션 비활성화)
- PostgreSQL 서비스가 백엔드 서비스에 **Connect** 되어 있어야 `DATABASE_URL` 자동 주입됨
- 환경변수: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `ANTHROPIC_API_KEY`, `NEWSAPI_KEY`

### Vercel 설정
- Root Directory: `frontend`
- 환경변수: `NEXT_PUBLIC_API_URL=https://agenda-supporter-production.up.railway.app`

---

## 파일 구조

```
C:\Agenda_supporter\
├── Dockerfile              ← 루트에 있어야 Railway가 인식
├── railway.json            ← 루트에 있어야 Railway가 인식
├── migrate.py              ← SQLite→PostgreSQL 마이그레이션 (1회성)
├── reclassify.py           ← DB 재분류 스크립트
├── CLASSIFICATION_RULES.md ← 분류 기준 문서
├── DASHBOARD_PLAN.md       ← 대시보드 설계 문서
├── backend/
│   ├── main.py             ← FastAPI 앱 + API 엔드포인트
│   ├── crawler.py          ← 네이버 API 크롤러 (섹션별 키워드)
│   ├── classifier.py       ← 키워드 룰 기반 분류기
│   ├── pipeline.py         ← 크롤링+분류+저장 파이프라인
│   ├── grouping.py         ← 유사 기사 그룹핑
│   ├── scheduler.py        ← 매일 09:00 KST 자동 수집
│   ├── models.py           ← SQLAlchemy DB 모델
│   └── requirements.txt
└── frontend/
    ├── app/
    │   └── page.tsx        ← Dashboard 렌더링
    ├── components/
    │   ├── Dashboard.tsx   ← 메인 대시보드 (날짜별 기사)
    │   ├── ManualCrawl.tsx ← 수동 수집 페이지
    │   ├── SavedArticles.tsx ← 저장된 기사 페이지
    │   ├── ArticleCard.tsx ← 기사 카드 컴포넌트
    │   └── StatCard.tsx    ← 통계 카드 컴포넌트
    └── lib/
        ├── api.ts          ← API 호출 함수
        └── types.ts        ← TypeScript 타입 정의
```

---

## 섹션 구조 (경전회의 3+1 섹션)

| 섹션 | 설명 | 분류 기준 |
|------|------|-----------|
| 섹션1_유통트렌드 | 정부정책·마케팅·ESG·조직문화 | 키워드 룰 (ESG/조직문화는 재계 기업명 필수) |
| 섹션2_반면교사 | 경쟁사 위기 사례 | 경쟁사명 + 위기 키워드 |
| 섹션3_당사관련 | 현대백화점그룹 계열사 기사 | 당사 기업명 in 제목 |
| 섹션4_경쟁사관련 | 경쟁사 일반 동향 | 경쟁사명 (위기 없음) |

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/dates` | 날짜 목록 (수동 진행 제외) |
| GET | `/articles?date=&section=` | 기사 목록 |
| GET | `/stats?date=` | 섹션별 통계 |
| POST | `/crawl` | 수동 수집 실행 (백그라운드) |
| POST | `/saved/{id}` | 기사 저장 |
| GET | `/saved` | 저장된 기사 목록 |
| DELETE | `/saved/{id}` | 저장 기사 삭제 |
| POST | `/admin/cleanup-unclassified` | 미분류 기사 DB 정리 |

---

## 자동 수집 스케줄

- **매일 09:00 KST** — `auto` 모드, 최근 7일치 수집, `collected_date = 오늘`
- **서버 최초 시작 시** — DB 비어있으면 `initial` 모드, 최근 14일치 수집
- **30일 지난 기사** — 자동 삭제

---

## 수동 수집 동작 방식

- 프론트엔드 **수동 수집** 버튼 클릭 → `/crawl` POST
- 백엔드에서 `days_back=1`로 크롤링, `collected_date = "수동 진행"` 저장
- 메인 대시보드 날짜 드롭박스에는 표시 안 됨 (별도 페이지에서 확인)
- 다음날 09:00 자동 수집 시 수동 진행 데이터 자동 삭제

---

## 분류기 주요 설계 결정

1. **Claude API 미사용** — 비용 절감, 키워드 룰 기반으로만 분류
2. **ESG_상생 / 조직문화_노동** — 재계 기업명 포함 시에만 섹션1 분류 (농협·지자체 오분류 방지)
3. **섹션2 반면교사** — 경쟁사명 + 위기 키워드 동시 존재 필수
4. **그룹핑** — 유사 기사 묶어서 그룹 카드로 표시

---

## 알려진 이슈 / 개선 여지

- [ ] **2026-03-22 데이터 오염**: 로컬 마이그레이션 데이터와 Railway 자동수집 데이터 혼재. 2026-03-23부터는 깔끔하게 분리됨
- [ ] **분류 정확도**: 키워드 룰 기반이라 완벽하지 않음. 오분류 발견 시 `classifier.py` 수정 후 `reclassify.py` 실행
- [ ] **수동 수집 중복**: `days_back=1`로 수집 시 이미 있는 기사는 중복 체크로 제외되지만, 당일 새 기사만 깔끔하게 뽑는 로직 개선 가능
- [ ] **SQLite 폴백**: 로컬 개발 시 `DATABASE_URL` 없으면 `agenda.db` 사용 (정상 동작)

---

## 다음에 할 수 있는 업그레이드

### 기능 개선
- [ ] 경전회의 보고서 자동 생성 (섹션별 표 형식 → 워드/PPT 다운로드)
- [ ] 기사 AI 메모 품질 개선 (Claude API 활용 옵션)
- [ ] 수동 수집 날짜/시간 범위 지정 기능
- [ ] 저장된 기사 → 섹션별 정렬/편집 기능

### 안정성
- [ ] 크롤링 실패 시 알림 (이메일 또는 슬랙)
- [ ] Railway 배포 상태 모니터링

---

## 로컬 개발 환경

```bash
# 백엔드
cd backend
uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs

# 프론트엔드
cd frontend
npm run dev
# → http://localhost:3000
```

`.env` 파일은 루트(`C:\Agenda_supporter\.env`)에 위치.

---

## DB 관련 스크립트

```bash
# SQLite → PostgreSQL 마이그레이션 (이미 완료)
py -3 migrate.py

# 기존 DB 재분류 (분류기 수정 후)
py -3 reclassify.py
```
