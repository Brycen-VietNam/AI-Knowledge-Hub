// Spec: docs/admin-spa/spec/admin-spa.spec.md#S004
// Task: T002 (S004) — metricsApi.ts — GET /v1/metrics (AC5)
import { apiClient } from './client'

export interface DailyQueryCount {
  date: string
  count: number
}

export interface MetricsData {
  documents: { total: number; ready: number; processing: number; error: number }
  users: { total: number; active: number }
  groups: { total: number }
  queries: { last_7_days: DailyQueryCount[] }
  health: { database: 'ok' | 'error'; api: 'ok' | 'error' }
}

export async function getMetrics(): Promise<MetricsData> {
  const res = await apiClient.get<MetricsData>('/v1/metrics')
  return res.data
}
