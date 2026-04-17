// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Task: T004 — LoginPage — centered layout wrapping LoginForm
// Task: S005/T002 — Replace inline styles with login-page CSS classes
import { LoginForm } from '../components/auth/LoginForm'

export function LoginPage() {
  return (
    <main className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <span className="login-brand-title">Knowledge Hub</span>
          <span className="login-brand-sub">BRYSEN GROUP</span>
        </div>
        <div className="login-body">
          <LoginForm />
        </div>
      </div>
    </main>
  )
}
