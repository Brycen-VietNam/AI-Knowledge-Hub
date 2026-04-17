// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T008 — DashboardPage — placeholder; S002–S004 will add full content
import { useTranslation } from 'react-i18next'
import { useAdminGuard } from '../hooks/useAdminGuard'

export function DashboardPage() {
  const { t } = useTranslation()
  useAdminGuard()

  return (
    <main className="dashboard-page">
      <h1>{t('nav.dashboard')}</h1>
    </main>
  )
}
