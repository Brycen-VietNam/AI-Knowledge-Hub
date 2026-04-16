// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Task: T004 — LoginPage — centered layout wrapping LoginForm
import { useTranslation } from 'react-i18next'
import { LoginForm } from '../components/auth/LoginForm'

export function LoginPage() {
  const { t } = useTranslation()
  return (
    <main style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
      <section>
        <h1>{t('app.title')}</h1>
        <LoginForm />
      </section>
    </main>
  )
}
