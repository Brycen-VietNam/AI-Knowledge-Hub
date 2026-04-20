// Spec: docs/admin-spa/spec/admin-spa.spec.md#S004
// Task: T004 (S004) — MetricCards — 4 KPI cards (AC2)
import { useTranslation } from 'react-i18next'
import type { MetricsData } from '../api/metricsApi'

interface Props {
  data: MetricsData
}

export function MetricCards({ data }: Props) {
  const { t } = useTranslation()
  return (
    <div className="metric-cards">
      <div className="metric-card">
        <span className="metric-card__label">{t('dashboard.total_docs')}</span>
        <span className="metric-card__value">{data.documents.total}</span>
      </div>
      <div className="metric-card">
        <span className="metric-card__label">{t('dashboard.active_docs')}</span>
        <span className="metric-card__value">{data.documents.ready}</span>
      </div>
      <div className="metric-card">
        <span className="metric-card__label">{t('dashboard.total_users')}</span>
        <span className="metric-card__value">{data.users.total}</span>
      </div>
      <div className="metric-card">
        <span className="metric-card__label">{t('dashboard.total_groups')}</span>
        <span className="metric-card__value">{data.groups.total}</span>
      </div>
    </div>
  )
}
