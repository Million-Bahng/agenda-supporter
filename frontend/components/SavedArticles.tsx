"use client"

import { useState, useEffect } from "react"
import { SavedArticle } from "@/lib/types"
import { fetchSavedArticles, clearSaved } from "@/lib/api"

const sectionStyle: Record<string, string> = {
  섹션1_유통트렌드: "bg-blue-50 text-blue-700",
  섹션2_반면교사:   "bg-red-50 text-red-700",
  섹션3_당사관련:   "bg-green-50 text-green-700",
  섹션4_경쟁사관련: "bg-purple-50 text-purple-700",
}

const sectionLabel: Record<string, string> = {
  섹션1_유통트렌드: "① 유통트렌드",
  섹션2_반면교사:   "② 반면교사",
  섹션3_당사관련:   "③ 당사관련",
  섹션4_경쟁사관련: "④ 경쟁사관련",
}

interface Props {
  onBack: () => void
}

export default function SavedArticles({ onBack }: Props) {
  const [articles, setArticles] = useState<SavedArticle[]>([])
  const [loading, setLoading] = useState(true)
  const [clearing, setClearing] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const data = await fetchSavedArticles()
      setArticles(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleClear = async () => {
    if (!confirm(`저장된 기사 ${articles.length}건을 모두 삭제하시겠습니까?`)) return
    setClearing(true)
    await clearSaved()
    setArticles([])
    setClearing(false)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800"
          >
            ← 돌아가기
          </button>
          <div className="text-center">
            <h1 className="text-xl font-bold text-gray-800">저장된 기사</h1>
            <p className="text-xs text-gray-400">{articles.length}건 보관 중</p>
          </div>
          <button
            onClick={handleClear}
            disabled={clearing || articles.length === 0}
            className="text-sm text-red-500 hover:text-red-700 border border-red-200 hover:border-red-400 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40"
          >
            {clearing ? "삭제 중..." : "비우기"}
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {loading && (
          <div className="text-center text-gray-400 py-16">로딩 중...</div>
        )}

        {!loading && articles.length === 0 && (
          <div className="text-center text-gray-400 py-16">
            저장된 기사가 없습니다.
            <br />
            <span className="text-sm">기사 카드의 &apos;기사 저장&apos; 버튼을 눌러 보관하세요.</span>
          </div>
        )}

        <div className="divide-y divide-gray-100">
          {articles.map((a) => (
            <div key={a.id} className="py-4">
              {/* 제목 */}
              <a
                href={a.link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-base font-semibold text-gray-800 hover:text-blue-600 leading-snug block mb-1"
              >
                {a.title}
              </a>

              {/* AI 메모 */}
              {a.ai_memo && (
                <p className="text-sm text-gray-600 bg-gray-50 rounded px-3 py-2 mb-2 leading-relaxed">
                  {a.ai_memo}
                </p>
              )}

              {/* 메타 */}
              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                <span className={`px-2 py-0.5 rounded font-medium ${sectionStyle[a.report_section] ?? "bg-gray-100 text-gray-600"}`}>
                  {sectionLabel[a.report_section] ?? a.report_section}
                </span>
                <span className="bg-gray-50 px-2 py-0.5 rounded">{a.category}</span>
                {a.related_company && a.related_company !== "해당없음" && (
                  <span className="bg-orange-50 text-orange-600 px-2 py-0.5 rounded">
                    {a.related_company}
                  </span>
                )}
                {a.outlet && (
                  <span className="bg-slate-50 text-slate-600 px-2 py-0.5 rounded">{a.outlet}</span>
                )}
                <span className="text-gray-400">{a.collected_date}</span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
