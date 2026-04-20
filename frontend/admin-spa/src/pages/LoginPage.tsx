// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T005 — LoginPage — centered layout with sessionExpiredMessage banner (AC6)
import { useTranslation } from 'react-i18next'
import { LoginForm } from '../components/auth/LoginForm'
import { useAuthStore } from '../store/authStore'

export function LoginPage() {
  const { t } = useTranslation()
  const { sessionExpiredMessage, clearSessionExpired } = useAuthStore()

  return (
    <main className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <span className="login-brand-title">{t('login.title')}</span>
          <span className="login-brand-sub">BRYSEN GROUP</span>
        </div>
        <div className="login-body">
          {sessionExpiredMessage && (
            <p role="alert" className="login-session-expired" onClick={clearSessionExpired}>
              {t('login.session_expired')}
            </p>
          )}
          <LoginForm />
        </div>
      </div>
    </main>
  )
}
