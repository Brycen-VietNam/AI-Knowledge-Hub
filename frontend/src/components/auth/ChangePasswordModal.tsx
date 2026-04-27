// Spec: docs/change-password/spec/change-password.spec.md#S003
// Spec: docs/security-audit/spec/security-audit.spec.md#S001
// Task: S003/T003 — ChangePasswordModal (self-service change, profile menu)
// Task: S001/T006 — handle 200+tokens response from PATCH; update authStore (D-SA-08)
// Rule: D6 — all CSS in index.css; no inline styles, no CSS modules, no Tailwind
// Decision: D1 — API-key callers excluded server-side; modal only for OIDC/password users
// Decision: D3 — OIDC users hidden from dropdown (App.tsx); modal never shown to them
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../../api/client'
import { useAuthStore } from '../../store/authStore'

interface ChangePasswordResponse {
  access_token: string
  refresh_token: string
  expires_in: number
}

interface Props {
  onClose: () => void
}

export function ChangePasswordModal({ onClose }: Props) {
  const { t } = useTranslation()
  const { login, username } = useAuthStore()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [confirmError, setConfirmError] = useState('')
  const [fieldError, setFieldError] = useState<string | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  function clearErrors() {
    setFieldError(null)
    setGeneralError(null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    clearErrors()

    // Client-side validation
    if (newPassword.length < 8) {
      setFieldError(t('auth.change_password.error.too_short'))
      return
    }
    if (newPassword !== confirmPassword) {
      setFieldError(t('auth.change_password.error.mismatch'))
      return
    }

    setIsLoading(true)
    try {
      const { data } = await apiClient.patch<ChangePasswordResponse>('/v1/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      login(data.access_token, data.refresh_token, username ?? '')
      setSuccessMsg(t('auth.change_password.success'))
      setTimeout(onClose, 1500)
    } catch (err: unknown) {
      const code =
        (err as { response?: { data?: { error?: { code?: string } } } })
          ?.response?.data?.error?.code
      if (code === 'ERR_WRONG_PASSWORD') {
        setFieldError(t('auth.change_password.error.wrong_password'))
      } else {
        setGeneralError(t('results.error_service'))
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="change-password-modal" role="dialog" aria-modal="true">
      <form className="change-password-form" onSubmit={handleSubmit}>
        <h2>{t('auth.change_password.title')}</h2>

        <div className="change-password-field">
          <label htmlFor="cp-current">{t('auth.change_password.current_password')}</label>
          <input
            id="cp-current"
            type="password"
            value={currentPassword}
            onChange={(e) => { clearErrors(); setCurrentPassword(e.target.value) }}
            required
            autoComplete="current-password"
          />
        </div>

        <div className="change-password-field">
          <label htmlFor="cp-new">{t('auth.change_password.new_password')}</label>
          <input
            id="cp-new"
            type="password"
            value={newPassword}
            maxLength={128}
            onChange={(e) => { clearErrors(); setNewPassword(e.target.value) }}
            required
            autoComplete="new-password"
          />
          <p className="field-hint">{t('auth.change_password.hint_password')}</p>
        </div>

        <div className="change-password-field">
          <label htmlFor="cp-confirm">{t('auth.change_password.confirm_password')}</label>
          <input
            id="cp-confirm"
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

        {fieldError && <p className="change-password-error">{fieldError}</p>}
        {generalError && <p className="change-password-error">{generalError}</p>}
        {successMsg && <p>{successMsg}</p>}

        <div className="change-password-actions">
          <button type="button" onClick={onClose} disabled={isLoading}>
            {t('auth.change_password.cancel')}
          </button>
          <button type="submit" disabled={isLoading}>
            {isLoading ? '…' : t('auth.change_password.submit')}
          </button>
        </div>
      </form>
    </div>
  )
}
