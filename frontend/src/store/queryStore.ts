// Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S002
// Task: T001 (S003) — submitQuery action + result/error states
// Task: T001,T004 (S004) — QueryHistoryItem + history state + addHistory in submitQuery
// Decision: D004 — query history session-only; D002 — token never in localStorage
import { create } from 'zustand'
import { apiClient } from '../api/client'

export interface Citation {
  doc_id: string
  title: string
  score: number
  chunk_preview: string
}

export interface QueryResult {
  answer: string
  citations: Citation[]
  confidence: number
}

export interface QueryHistoryItem {
  id: string
  query: string
  answer: string
  citations: Citation[]
  timestamp: Date
}

interface QueryState {
  query: string
  isLoading: boolean
  error: string | null
  result: QueryResult | null
  history: QueryHistoryItem[]
  setQuery: (q: string) => void
  setLoading: (b: boolean) => void
  setError: (e: string | null) => void
  reset: () => void
  submitQuery: (query: string, lang: string) => Promise<void>
  addHistory: (query: string, answer: string, citations: Citation[]) => void
  clearHistory: () => void
  selectHistory: (item: QueryHistoryItem) => void
}

export const useQueryStore = create<QueryState>((set, get) => ({
  query: '',
  isLoading: false,
  error: null,
  result: null,
  history: [],

  setQuery: (q) => set({ query: q }),
  setLoading: (b) => set({ isLoading: b }),
  setError: (e) => set({ error: e }),

  reset: () => set({ query: '', isLoading: false, error: null, result: null }),

  addHistory: (query, answer, citations) =>
    set((s) => ({
      history: [
        { id: crypto.randomUUID(), query, answer, citations, timestamp: new Date() },
        ...s.history,
      ].slice(0, 20),
    })),

  clearHistory: () => set({ history: [] }),

  selectHistory: (item) =>
    set({
      query: item.query,
      result: { answer: item.answer, citations: item.citations, confidence: 0 },
      error: null,
    }),

  submitQuery: async (query: string, lang: string) => {
    set({ isLoading: true, error: null, result: null })
    try {
      const response = await apiClient.post<QueryResult>('/v1/query', { query, lang })
      set({ result: response.data })
      const { answer, citations } = response.data
      get().addHistory(query, answer, citations)
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 429) {
        set({ error: 'results.error_rate_limit' })
      } else {
        set({ error: 'results.error_service' })
      }
    } finally {
      set({ isLoading: false })
    }
  },
}))
