import { Article, SavedArticle, Stats, DateEntry } from "./types"

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ─────────────────────────────────────────────
// 날짜 목록
// ─────────────────────────────────────────────

export async function fetchDates(): Promise<DateEntry[]> {
  const res = await fetch(`${BASE}/dates`, { cache: "no-store" })
  return res.json()
}

// ─────────────────────────────────────────────
// 통계
// ─────────────────────────────────────────────

export async function fetchStats(date?: string): Promise<Stats> {
  const q = date ? `?date=${encodeURIComponent(date)}` : ""
  const res = await fetch(`${BASE}/stats${q}`, { cache: "no-store" })
  return res.json()
}

// ─────────────────────────────────────────────
// 기사 목록
// ─────────────────────────────────────────────

export async function fetchArticles(params?: {
  date?: string
  section?: string
  limit?: number
}): Promise<Article[]> {
  const q = new URLSearchParams()
  if (params?.date) q.set("date", params.date)
  if (params?.section) q.set("section", params.section)
  q.set("limit", String(params?.limit ?? 200))

  const res = await fetch(`${BASE}/articles?${q}`, { cache: "no-store" })
  return res.json()
}

// ─────────────────────────────────────────────
// 크롤링
// ─────────────────────────────────────────────

export async function triggerCrawl(): Promise<{ message: string }> {
  const res = await fetch(`${BASE}/crawl`, { method: "POST" })
  return res.json()
}

// ─────────────────────────────────────────────
// 저장 기사
// ─────────────────────────────────────────────

export async function fetchSavedArticles(): Promise<SavedArticle[]> {
  const res = await fetch(`${BASE}/saved`, { cache: "no-store" })
  return res.json()
}

export async function fetchSavedIds(): Promise<number[]> {
  const res = await fetch(`${BASE}/saved/ids`, { cache: "no-store" })
  return res.json()
}

export async function saveArticle(articleId: number): Promise<{ message: string }> {
  const res = await fetch(`${BASE}/saved/${articleId}`, { method: "POST" })
  return res.json()
}

export async function deleteSavedArticle(articleId: number): Promise<{ message: string }> {
  const res = await fetch(`${BASE}/saved/${articleId}`, { method: "DELETE" })
  return res.json()
}

export async function clearSaved(): Promise<{ message: string }> {
  const res = await fetch(`${BASE}/saved`, { method: "DELETE" })
  return res.json()
}
