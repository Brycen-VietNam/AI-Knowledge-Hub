// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Task: T004 — LoginForm — OAuth2 form POST + authStore login + proactive refresh
// Decision: T004 analysis — URLSearchParams (not JSON); backend: OAuth2PasswordRequestForm
import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../../api/client'
import { useAuthStore } from '../../store/authStore'

interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export function LoginForm() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { login, scheduleRefresh } = useAuthStore()

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
      login(data.access_token, username, password)
      const expSeconds = Date.now() / 1000 + data.expires_in
      scheduleRefresh(expSeconds, async () => {
        try {
          const refreshBody = new URLSearchParams({ username, password })
          const { data: refreshData } = await apiClient.post<TokenResponse>(
            '/v1/auth/token',
            refreshBody,
            { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
          )
          login(refreshData.access_token, username, password)
          const nextExp = Date.now() / 1000 + refreshData.expires_in
          scheduleRefresh(nextExp, () => {})
        } catch {
          // refresh failed → 401 interceptor handles logout
        }
      })
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
    <form onSubmit={handleSubmit} aria-label="login-form">
      <div>
        <label htmlFor="username">{t('login.username')}</label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          autoComplete="username"
        />
      </div>
      <div>
        <label htmlFor="password">{t('login.password')}</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
      </div>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={isLoading}>
        {t('login.submit')}
      </button>
    </form>
  )
}
