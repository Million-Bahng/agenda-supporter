"use client"

import { useState } from "react"
import { Article } from "@/lib/types"
import { saveArticle, deleteSavedArticle } from "@/lib/api"

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
  article: Article
  isSaved: boolean
  onSaveToggle: (id: number, saved: boolean) => void
  compact?: boolean
}

export default function ArticleCard({ article, isSaved, onSaveToggle, compact = false }: Props) {
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (isSaved || saving) return
    setSaving(true)
    try {
      await saveArticle(article.id)
      onSaveToggle(article.id, true)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow ${compact ? "p-4" : "p-5"}`}>
      {/* 제목 */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <a
          href={article.link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-base font-semibold text-gray-800 hover:text-blue-600 leading-snug flex-1"
        >
          {article.title}
        </a>
      </div>

      {/* AI 메모 */}
      {article.ai_memo && (
        <p className="text-sm text-gray-600 bg-gray-50 rounded-lg px-3 py-2 mb-3 leading-relaxed">
          {article.ai_memo}
        </p>
      )}

      {/* 하단 메타 */}
      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
        {/* 섹션 뱃지 */}
        <span className={`px-2 py-0.5 rounded font-medium ${sectionStyle[article.report_section] ?? "bg-gray-100 text-gray-600"}`}>
          {sectionLabel[article.report_section] ?? article.report_section}
        </span>

        {/* 카테고리 */}
        <span className="bg-gray-50 px-2 py-0.5 rounded">{article.category}</span>

        {/* 관련기업 */}
        {article.related_company && article.related_company !== "해당없음" && (
          <span className="bg-orange-50 text-orange-600 px-2 py-0.5 rounded">
            {article.related_company}
          </span>
        )}

        {/* 매체명 */}
        {article.outlet && (
          <span className="bg-slate-50 text-slate-600 px-2 py-0.5 rounded">
            {article.outlet}
          </span>
        )}

        {/* 수집일자 */}
        <span className="ml-auto text-gray-400">{article.collected_date}</span>

        {/* 기사 저장 버튼 */}
        <button
          onClick={handleSave}
          disabled={isSaved || saving}
          className={`px-3 py-0.5 rounded border transition-colors ${
            isSaved
              ? "border-gray-200 text-gray-400 cursor-default"
              : "border-blue-300 text-blue-600 hover:bg-blue-50"
          }`}
        >
          {saving ? "저장 중..." : isSaved ? "저장됨" : "기사 저장"}
        </button>
      </div>
    </div>
  )
}
