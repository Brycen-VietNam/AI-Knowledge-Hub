// Spec: docs/admin-spa/spec/admin-spa.spec.md#S004
// Task: T007 (S004) — DashboardPage — Metrics dashboard (AC1–AC7)
import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useAdminGuard } from '../hooks/useAdminGuard'
import { useAutoRefresh } from '../hooks/useAutoRefresh'
import { getMetrics } from '../api/metricsApi'
import type { MetricsData } from '../api/metricsApi'
import { MetricCards } from '../components/MetricCards'
import { QueryVolumeChart } from '../components/QueryVolumeChart'
import { HealthIndicators } from '../components/HealthIndicators'

export function DashboardPage() {
  const { t } = useTranslation()
  useAdminGuard()
  const [data, setData] = useState<MetricsData | null>(null)
  const [error, setError] = useState(false)

  const fetchMetrics = useCallback(async () => {
    try {
      const result = await getMetrics()
      setData(result)
      setError(false)
    } catch {
      setError(true)
    }
  }, [])

  useAutoRefresh(fetchMetrics, 60_000)

  return (
    <main className="dashboard-page">
      <h1>{t('nav.dashboard')}</h1>
      {error && (
        <p className="metrics-unavailable">{t('dashboard.metrics_unavailable')}</p>
      )}
      {data && (
        <>
          <MetricCards data={data} />
          <QueryVolumeChart data={data.queries.last_7_days} />
          <HealthIndicators health={data.health} />
        </>
      )}
    </main>
  )
}

