export interface Article {
  id: number
  title: string
  link: string
  outlet: string
  description: string
  pub_date: string
  collected_date: string
  report_section: string
  category: string
  relevance_score: number
  importance: "상" | "중" | "하"
  related_company: string
  is_competitor: boolean
  ai_memo: string
  group_id: string | null
}

export interface SavedArticle {
  id: number
  article_id: number
  title: string
  link: string
  outlet: string
  description: string
  pub_date: string
  collected_date: string
  report_section: string
  category: string
  related_company: string
  is_competitor: boolean
  ai_memo: string
  saved_at: string
}

export interface Stats {
  total: number
  competitor_cases: number
  by_section: {
    섹션1_유통트렌드: number
    섹션2_반면교사: number
    섹션3_당사관련: number
    섹션4_경쟁사관련: number
  }
}

export interface DateEntry {
  date: string   // "YYYY-MM-DD" 또는 "수동 진행"
  count: number
}
