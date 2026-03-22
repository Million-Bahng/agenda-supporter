"use client"

import { useState, useEffect, useCallback } from "react"
import { Article, Stats, DateEntry } from "@/lib/types"
import { fetchArticles, fetchStats, fetchDates, triggerCrawl, fetchSavedIds } from "@/lib/api"
import StatCard from "./StatCard"
import ArticleCard from "./ArticleCard"
import SavedArticles from "./SavedArticles"

const SECTIONS = [
  { key: "", label: "전체" },
  { key: "섹션1_유통트렌드", label: "① 유통트렌드" },
  { key: "섹션2_반면교사", label: "② 반면교사" },
  { key: "섹션3_당사관련", label: "③ 당사관련" },
  { key: "섹션4_경쟁사관련", label: "④ 경쟁사관련" },
]

export default function Dashboard() {
  const [view, setView] = useState<"dashboard" | "saved">("dashboard")
  const [dates, setDates] = useState<DateEntry[]>([])
  const [selectedDate, setSelectedDate] = useState<string>("")
  const [stats, setStats] = useState<Stats | null>(null)
  const [articles, setArticles] = useState<Article[]>([])
  const [section, setSection] = useState("")
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(false)
  const [crawling, setCrawling] = useState(false)
  const [toast, setToast] = useState("")

  // 날짜 목록 로드
  const loadDates = useCallback(async () => {
    const d = await fetchDates()
    setDates(d)
    return d
  }, [])

  // 기사+통계 로드
  const loadData = useCallback(async (date: string, sec: string) => {
    setLoading(true)
    try {
      const [s, a, ids] = await Promise.all([
        fetchStats(date || undefined),
        fetchArticles({ date: date || undefined, section: sec || undefined }),
        fetchSavedIds(),
      ])
      setStats(s)
      setArticles(a)
      setSavedIds(new Set(ids))
    } finally {
      setLoading(false)
    }
  }, [])

  // 초기 로드
  useEffect(() => {
    loadDates().then((d) => {
      const first = d[0]?.date ?? ""
      setSelectedDate(first)
      loadData(first, "")
    })
  }, [loadDates, loadData])

  // 날짜/섹션 변경 시 재로드
  useEffect(() => {
    if (selectedDate !== undefined) {
      loadData(selectedDate, section)
    }
  }, [selectedDate, section, loadData])

  const handleCrawl = async () => {
    setCrawling(true)
    const res = await triggerCrawl()
    setToast(res.message)
    setTimeout(() => setToast(""), 4000)

    // 5초 후 날짜 목록 갱신 → "수동 진행"으로 전환
    setTimeout(async () => {
      const d = await loadDates()
      const manual = d.find((e) => e.date === "수동 진행")
      if (manual) {
        setSelectedDate("수동 진행")
      }
      setCrawling(false)
    }, 5000)
  }

  const handleSaveToggle = async (articleId: number, saved: boolean) => {
    setSavedIds((prev) => {
      const next = new Set(prev)
      if (saved) next.add(articleId)
      else next.delete(articleId)
      return next
    })
  }

  if (view === "saved") {
    return (
      <SavedArticles
        onBack={() => {
          setView("dashboard")
          loadData(selectedDate, section)
        }}
      />
    )
  }

  // 섹션 필터링된 기사 (그룹핑 포함)
  const displayArticles = section
    ? articles.filter((a) => a.report_section === section)
    : articles

  // 그룹핑 처리
  const grouped = groupArticles(displayArticles)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div className="shrink-0">
            <h1 className="text-xl font-bold text-gray-800">경전회의 기사 대시보드</h1>
            <p className="text-xs text-gray-400 mt-0.5">현대백화점그룹 홍보실</p>
          </div>

          <div className="flex items-center gap-3 flex-wrap justify-end">
            {/* 날짜 드롭박스 */}
            <select
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white text-gray-700 cursor-pointer"
            >
              {dates.length === 0 && (
                <option value="">날짜 없음</option>
              )}
              {dates.map((d) => (
                <option key={d.date} value={d.date}>
                  {d.date === "수동 진행" ? `수동 진행 (${d.count}건)` : `${d.date} (${d.count}건)`}
                </option>
              ))}
            </select>

            <button
              onClick={() => setView("saved")}
              className="text-sm text-gray-600 hover:text-gray-800 border border-gray-200 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors whitespace-nowrap"
            >
              저장된 기사 보기
            </button>

            <button
              onClick={handleCrawl}
              disabled={crawling}
              className="text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white px-4 py-2 rounded-lg transition-colors whitespace-nowrap"
            >
              {crawling ? "수집 중..." : "기사 수집"}
            </button>
          </div>
        </div>
      </header>

      {toast && (
        <div className="fixed top-20 right-6 bg-green-600 text-white text-sm px-4 py-2 rounded-lg shadow-lg z-50">
          {toast}
        </div>
      )}

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {/* 통계 카드 4개 */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="전체 기사" value={stats.total} />
            <StatCard
              label="② 반면교사"
              value={stats.by_section["섹션2_반면교사"]}
              sub="위기 사례"
              color="bg-orange-50"
            />
            <StatCard
              label="③ 당사 관련"
              value={stats.by_section["섹션3_당사관련"]}
              sub="모니터링 필요"
              color="bg-blue-50"
            />
            <StatCard
              label="④ 경쟁사 동향"
              value={stats.by_section["섹션4_경쟁사관련"]}
              sub="일반 동향"
              color="bg-purple-50"
            />
          </div>
        )}

        {/* 섹션별 분포 바 */}
        {stats && stats.total > 0 && (
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <p className="text-sm font-semibold text-gray-600 mb-3">섹션별 분포</p>
            <div className="flex gap-4 text-sm">
              {[
                { label: "① 유통트렌드", key: "섹션1_유통트렌드", color: "bg-blue-500" },
                { label: "② 반면교사",   key: "섹션2_반면교사",   color: "bg-red-500"  },
                { label: "③ 당사관련",   key: "섹션3_당사관련",   color: "bg-green-500"},
                { label: "④ 경쟁사관련", key: "섹션4_경쟁사관련", color: "bg-purple-500"},
              ].map(({ label, key, color }) => {
                const count = stats.by_section[key as keyof typeof stats.by_section] ?? 0
                const pct = stats.total ? Math.round((count / stats.total) * 100) : 0
                return (
                  <div key={key} className="flex-1">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>{label}</span>
                      <span>{count}건 ({pct}%)</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* 섹션 필터 탭 */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex gap-1 bg-white border border-gray-200 rounded-lg p-1">
            {SECTIONS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setSection(key)}
                className={`text-sm px-3 py-1.5 rounded-md transition-colors ${
                  section === key
                    ? "bg-blue-600 text-white"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <span className="text-sm text-gray-400 ml-auto">
            {loading ? "로딩 중..." : `${displayArticles.length}건`}
          </span>
        </div>

        {/* 기사 목록 (그룹 포함) */}
        <div className="space-y-3">
          {displayArticles.length === 0 && !loading && (
            <div className="text-center text-gray-400 py-16">
              {dates.length === 0
                ? "서버 시작 후 초기 수집 중입니다. 잠시 후 새로고침 해주세요."
                : "기사가 없습니다."}
            </div>
          )}
          {grouped.map((item) =>
            item.type === "single" ? (
              <ArticleCard
                key={item.article.id}
                article={item.article}
                isSaved={savedIds.has(item.article.id)}
                onSaveToggle={handleSaveToggle}
              />
            ) : (
              <GroupCard
                key={item.groupId}
                groupId={item.groupId}
                articles={item.articles}
                savedIds={savedIds}
                onSaveToggle={handleSaveToggle}
              />
            )
          )}
        </div>
      </main>
    </div>
  )
}


// ─────────────────────────────────────────────
// 그룹 카드 컴포넌트
// ─────────────────────────────────────────────

interface GroupCardProps {
  groupId: string
  articles: Article[]
  savedIds: Set<number>
  onSaveToggle: (id: number, saved: boolean) => void
}

function GroupCard({ groupId, articles, savedIds, onSaveToggle }: GroupCardProps) {
  const [expanded, setExpanded] = useState(false)
  const rep = articles[0]

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full text-left px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-bold bg-gray-100 text-gray-600 px-2 py-0.5 rounded shrink-0">
            그룹 {articles.length}건
          </span>
          <span className="text-sm font-semibold text-gray-700 truncate">
            {rep.title}
          </span>
        </div>
        <span className="text-gray-400 text-sm ml-3 shrink-0">
          {expanded ? "▲ 접기" : "▶ 펼치기"}
        </span>
      </button>

      {expanded && (
        <div className="border-t border-gray-100 divide-y divide-gray-50">
          {articles.map((a) => (
            <div key={a.id} className="px-5 py-1">
              <ArticleCard
                article={a}
                isSaved={savedIds.has(a.id)}
                onSaveToggle={onSaveToggle}
                compact
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


// ─────────────────────────────────────────────
// 그룹핑 헬퍼
// ─────────────────────────────────────────────

type GroupedItem =
  | { type: "single"; article: Article }
  | { type: "group"; groupId: string; articles: Article[] }

function groupArticles(articles: Article[]): GroupedItem[] {
  const groups: Map<string, Article[]> = new Map()
  const singles: Article[] = []

  for (const a of articles) {
    if (!a.group_id) {
      singles.push(a)
    } else {
      if (!groups.has(a.group_id)) groups.set(a.group_id, [])
      groups.get(a.group_id)!.push(a)
    }
  }

  const result: GroupedItem[] = []

  // 그룹이 실제로 2건 이상일 때만 그룹 카드로 표시
  for (const [groupId, arts] of groups) {
    if (arts.length >= 2) {
      result.push({ type: "group", groupId, articles: arts })
    } else {
      singles.push(arts[0])
    }
  }

  // 단독 기사
  for (const a of singles) {
    result.push({ type: "single", article: a })
  }

  return result
}
