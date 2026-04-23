// Spec: docs/change-password/spec/change-password.spec.md#S005
// Task: S005/T004 — Force-change gate page (first login after admin password set)
// Decision: D5 — no current-password field; authStore.password used silently
// Decision: D6 — all CSS in index.css; no inline styles, no CSS modules, no Tailwind
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../api/client'
import { useAuthStore } from '../store/authStore'

export function ChangePasswordPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { password: currentPassword, clearMustChangePassword } = useAuthStore()

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
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
      await apiClient.patch('/v1/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      clearMustChangePassword()
      navigate('/')
    } catch {
      setError(t('results.error_service'))
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
            <label htmlFor="fc-new">{t('auth.force_change.new_password')}</label>
            <input
              id="fc-new"
              type="password"
              value={newPassword}
              onChange={(e) => { setError(null); setNewPassword(e.target.value) }}
              required
              autoComplete="new-password"
            />
          </div>
          <div>
            <label htmlFor="fc-confirm">{t('auth.force_change.confirm_password')}</label>
            <input
              id="fc-confirm"
              type="password"
              value={confirmPassword}
              onChange={(e) => { setError(null); setConfirmPassword(e.target.value) }}
              required
              autoComplete="new-password"
            />
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
