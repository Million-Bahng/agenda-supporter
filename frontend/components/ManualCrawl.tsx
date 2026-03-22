"use client"

import { useState, useEffect, useCallback } from "react"
import { Article } from "@/lib/types"
import { fetchArticles, fetchSavedIds, triggerCrawl } from "@/lib/api"
import ArticleCard from "./ArticleCard"

const SECTIONS = [
  { key: "", label: "전체" },
  { key: "섹션1_유통트렌드", label: "① 유통트렌드" },
  { key: "섹션2_반면교사", label: "② 반면교사" },
  { key: "섹션3_당사관련", label: "③ 당사관련" },
  { key: "섹션4_경쟁사관련", label: "④ 경쟁사관련" },
]

interface Props {
  onBack: () => void
}

export default function ManualCrawl({ onBack }: Props) {
  const [articles, setArticles] = useState<Article[]>([])
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set())
  const [section, setSection] = useState("")
  const [loading, setLoading] = useState(true)
  const [crawling, setCrawling] = useState(false)
  const [toast, setToast] = useState("")

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [a, ids] = await Promise.all([
        fetchArticles({ date: "수동 진행" }),
        fetchSavedIds(),
      ])
      setArticles(a)
      setSavedIds(new Set(ids))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const handleCrawl = async () => {
    setCrawling(true)
    const res = await triggerCrawl()
    setToast(res.message)
    setTimeout(() => setToast(""), 4000)

    // 10초마다 수동 진행 데이터 확인 (최대 3분)
    let attempts = 0
    const poll = async () => {
      attempts++
      const a = await fetchArticles({ date: "수동 진행" })
      if (a.length > 0) {
        const ids = await fetchSavedIds()
        setArticles(a)
        setSavedIds(new Set(ids))
        setCrawling(false)
      } else if (attempts < 18) {
        setTimeout(poll, 10000)
      } else {
        setCrawling(false)
      }
    }
    setTimeout(poll, 10000)
  }

  const handleSaveToggle = (articleId: number, saved: boolean) => {
    setSavedIds((prev) => {
      const next = new Set(prev)
      if (saved) next.add(articleId)
      else next.delete(articleId)
      return next
    })
  }

  const displayArticles = section
    ? articles.filter((a) => a.report_section === section)
    : articles

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800 shrink-0"
          >
            ← 돌아가기
          </button>
          <div className="text-center">
            <h1 className="text-xl font-bold text-gray-800">수동 수집</h1>
            <p className="text-xs text-gray-400">오늘 오전 9시 이후 최신 기사</p>
          </div>
          <button
            onClick={handleCrawl}
            disabled={crawling}
            className="text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white px-4 py-2 rounded-lg transition-colors whitespace-nowrap shrink-0"
          >
            {crawling ? "수집 중..." : "기사 수집"}
          </button>
        </div>
      </header>

      {toast && (
        <div className="fixed top-20 right-6 bg-green-600 text-white text-sm px-4 py-2 rounded-lg shadow-lg z-50">
          {toast}
        </div>
      )}

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
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

        {/* 기사 목록 */}
        <div className="space-y-3">
          {!loading && articles.length === 0 && (
            <div className="text-center text-gray-400 py-16">
              수동 수집 결과가 없습니다.
              <br />
              <span className="text-sm">기사 수집 버튼을 눌러 최신 기사를 가져오세요.</span>
            </div>
          )}
          {displayArticles.map((a) => (
            <ArticleCard
              key={a.id}
              article={a}
              isSaved={savedIds.has(a.id)}
              onSaveToggle={handleSaveToggle}
            />
          ))}
        </div>
      </main>
    </div>
  )
}
