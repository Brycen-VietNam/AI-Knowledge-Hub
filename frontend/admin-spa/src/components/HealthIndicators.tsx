// Spec: docs/admin-spa/spec/admin-spa.spec.md#S004
// Task: T006 (S004) — HealthIndicators — DB + API health status (AC4)
import { useTranslation } from 'react-i18next'
import type { MetricsData } from '../api/metricsApi'

interface BadgeProps {
  label: string
  status: 'ok' | 'error'
}

function HealthBadge({ label, status }: BadgeProps) {
  const { t } = useTranslation()
  return (
    <div className={`health-badge health-badge--${status}`}>
      <span className="health-dot" />
      <span>
        {label}: {status === 'ok' ? t('dashboard.health_ok') : t('dashboard.health_error')}
      </span>
    </div>
  )
}

interface Props {
  health: MetricsData['health']
}

export function HealthIndicators({ health }: Props) {
  const { t } = useTranslation()
  return (
    <div className="health-indicators">
      <h2 className="health-title">{t('dashboard.health_title')}</h2>
      <HealthBadge label={t('dashboard.health_db')} status={health.database} />
      <HealthBadge label={t('dashboard.health_api')} status={health.api} />
    </div>
  )
}
