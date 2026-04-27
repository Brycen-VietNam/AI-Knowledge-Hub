// Spec: docs/change-password/spec/change-password.spec.md#S005
// Spec: docs/security-audit/spec/security-audit.spec.md#S001
// Task: S005/T004 — Force-change gate page (first login after admin password set)
// Task: S001/T006 — remove authStore.password; add explicit current-password input (Option A)
// Task: S001/T007 — handle 200+tokens response from PATCH; update authStore
// Decision: D5 (updated) — Option A: user types temporary password explicitly
// Decision: D6 — all CSS in index.css; no inline styles, no CSS modules, no Tailwind
// Decision: D-SA-08 — PATCH returns 200+tokens; authStore updated (no UX disruption)
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../api/client'
import { useAuthStore } from '../store/authStore'

interface ChangePasswordResponse {
  access_token: string
  refresh_token: string
  expires_in: number
}

export function ChangePasswordPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { login, clearMustChangePassword, username, scheduleRefresh, refreshAccessToken } = useAuthStore()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [confirmError, setConfirmError] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (newPassword.length < 8) {
      setError(t('auth.force_change.error.too_short'))
      return
    }
    if (newPassword !== confirmPassword) {
      setError(t('auth.force_change.error.mismatch'))
      return
    }

    setIsLoading(true)
    try {
      const { data } = await apiClient.patch<ChangePasswordResponse>('/v1/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      login(data.access_token, data.refresh_token, username ?? '')
      const nextExp = Date.now() / 1000 + data.expires_in
      scheduleRefresh(nextExp, () => refreshAccessToken())
      clearMustChangePassword()
      navigate('/')
    } catch (err: unknown) {
      const code =
        (err as { response?: { data?: { error?: { code?: string } } } })
          ?.response?.data?.error?.code
      if (code === 'ERR_WRONG_PASSWORD') {
        setError(t('auth.change_password.error.wrong_password'))
      } else {
        setError(t('results.error_service'))
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="force-change-page">
      <div className="force-change-card">
        <h1 className="force-change-title">{t('auth.force_change.title')}</h1>
        <p className="force-change-notice">{t('auth.force_change.notice')}</p>
        <form className="force-change-form" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="fc-current">{t('auth.force_change.current_password')}</label>
            <input
              id="fc-current"
              type="password"
              value={currentPassword}
              onChange={(e) => { setError(null); setCurrentPassword(e.target.value) }}
              required
              autoComplete="current-password"
            />
          </div>
          <div>
            <label htmlFor="fc-new">{t('auth.force_change.new_password')}</label>
            <input
              id="fc-new"
              type="password"
              value={newPassword}
              maxLength={128}
              onChange={(e) => { setError(null); setNewPassword(e.target.value) }}
              required
              autoComplete="new-password"
            />
            <p className="field-hint">{t('auth.change_password.hint_password')}</p>
          </div>
          <div>
            <label htmlFor="fc-confirm">{t('auth.force_change.confirm_password')}</label>
            <input
              id="fc-confirm"
              type="password"
              value={confirmPassword}
              maxLength={128}
              onChange={(e) => {
                const v = e.target.value
                setConfirmPassword(v)
                if (v && v !== newPassword) {
                  setConfirmError(t('auth.change_password.error.mismatch'))
                } else {
                  setConfirmError('')
                }
              }}
              required
              autoComplete="new-password"
            />
            {confirmError && <p className="field-error">{confirmError}</p>}
          </div>
          {error && <p role="alert">{error}</p>}
          <button
            type="submit"
            className="force-change-submit"
            disabled={isLoading}
          >
            {isLoading ? '…' : t('auth.force_change.submit')}
          </button>
        </form>
      </div>
    </main>
  )
}
