// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Spec: docs/security-audit/spec/security-audit.spec.md#S001
// Task: T004 — LoginForm — OAuth2 form POST + authStore login + proactive refresh
// Task: S001/T006 — remove password arg from login(); replace inline re-login with refreshAccessToken
// Decision: T004 analysis — URLSearchParams (not JSON); backend: OAuth2PasswordRequestForm
// Decision: D-SA-02 — password never stored; refresh via token only (DEFERRED-SEC-001 fix)
import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../../api/client'
import { useAuthStore } from '../../store/authStore'

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  must_change_password?: boolean
}

export function LoginForm() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { login, scheduleRefresh, refreshAccessToken } = useAuthStore()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const body = new URLSearchParams({ username, password })
      const { data } = await apiClient.post<TokenResponse>('/v1/auth/token', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      login(data.access_token, data.refresh_token, username, data.must_change_password ?? false)
      const expSeconds = Date.now() / 1000 + data.expires_in
      scheduleRefresh(expSeconds, () => refreshAccessToken())
      navigate('/query')
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 401) {
        setError(t('login.error_invalid'))
      } else {
        setError(t('login.error_unavailable'))
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} aria-label="login-form" className="login-form">
      <div className="form-group">
        <label htmlFor="username" className="form-label">{t('login.username')}</label>
        <input
          id="username"
          type="text"
          className="form-input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          autoComplete="username"
        />
      </div>
      <div className="form-group">
        <label htmlFor="password" className="form-label">{t('login.password')}</label>
        <input
          id="password"
          type="password"
          className="form-input"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
      </div>
      {error && <p role="alert" className="login-error">{error}</p>}
      <button type="submit" className="btn-primary" disabled={isLoading}>
        {t('login.submit')}
      </button>
    </form>
  )
}
