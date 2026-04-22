// Spec: docs/change-password/spec/change-password.spec.md#S004
// Task: S004/T003 — ResetPasswordModal (admin force-reset; generate or manual)
// Rule: D6 — all CSS in index.css; no inline styles, no CSS modules, no Tailwind
// Decision: D2 — generate → 200 + {password}; manual → 204
// Decision: D3 — OIDC users (has_password=false) hidden at row level (UsersTab)
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../../api/client'

interface Props {
  userId: string
  onClose: () => void
}

export function ResetPasswordModal({ userId, onClose }: Props) {
  const { t } = useTranslation()

  const [mode, setMode] = useState<'generate' | 'manual'>('generate')
  const [newPassword, setNewPassword] = useState('')
  const [generatedPassword, setGeneratedPassword] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
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

    if (mode === 'manual' && newPassword.length < 8) {
      setFieldError(t('auth.reset_password.error.too_short'))
      return
    }

    setIsLoading(true)
    try {
      const body = mode === 'generate' ? { generate: true } : { new_password: newPassword }
      const res = await apiClient.post(`/v1/admin/users/${userId}/password-reset`, body)

      if (mode === 'generate') {
        const data = res as { data?: { password?: string } }
        setGeneratedPassword(data?.data?.password ?? (res as unknown as { password?: string }).password ?? '')
      }
      setSuccessMsg(t('auth.reset_password.success'))
      if (mode === 'manual') {
        setTimeout(onClose, 1500)
      }
    } catch (err: unknown) {
      const code =
        (err as { response?: { data?: { error?: { code?: string } } } })
          ?.response?.data?.error?.code
      if (code === 'ERR_PASSWORD_NOT_APPLICABLE') {
        setGeneralError(t('auth.reset_password.error.oidc_not_applicable'))
      } else {
        setGeneralError(t('results.error_service'))
      }
    } finally {
      setIsLoading(false)
    }
  }

  function handleCopy() {
    if (generatedPassword) {
      navigator.clipboard.writeText(generatedPassword).then(() => {
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      })
    }
  }

  return (
    <div className="reset-password-modal" role="dialog" aria-modal="true">
      <form className="change-password-form" onSubmit={handleSubmit}>
        <h2>{t('auth.reset_password.title')}</h2>

        <div className="reset-password-options">
          <label>
            <input
              type="radio"
              name="reset-mode"
              value="generate"
              checked={mode === 'generate'}
              onChange={() => { setMode('generate'); clearErrors() }}
            />
            {t('auth.reset_password.option_generate')}
          </label>
          <label>
            <input
              type="radio"
              name="reset-mode"
              value="manual"
              checked={mode === 'manual'}
              onChange={() => { setMode('manual'); clearErrors() }}
            />
            {t('auth.reset_password.option_manual')}
          </label>
        </div>

        {mode === 'manual' && (
          <div className="change-password-field">
            <label htmlFor="rp-new">{t('auth.reset_password.new_password')}</label>
            <input
              id="rp-new"
              type="password"
              value={newPassword}
              onChange={(e) => { clearErrors(); setNewPassword(e.target.value) }}
              required
              autoComplete="new-password"
            />
          </div>
        )}

        {generatedPassword && (
          <>
            <div>
              <label>{t('auth.reset_password.generated_label')}</label>
              <div className="reset-password-generated">
                <input type="text" value={generatedPassword} readOnly />
                <button type="button" className="reset-password-copy-btn" onClick={handleCopy}>
                  {copied ? '✓' : t('auth.reset_password.copy')}
                </button>
              </div>
            </div>
            <p className="reset-password-warning">{t('auth.reset_password.warning')}</p>
          </>
        )}

        {fieldError && <p className="change-password-error">{fieldError}</p>}
        {generalError && <p className="change-password-error">{generalError}</p>}
        {successMsg && !generatedPassword && <p>{successMsg}</p>}

        <div className="reset-password-actions">
          <button type="button" onClick={onClose} disabled={isLoading}>
            {t('auth.reset_password.cancel')}
          </button>
          {!generatedPassword && (
            <button type="submit" disabled={isLoading}>
              {isLoading ? '…' : t('auth.reset_password.submit')}
            </button>
          )}
          {generatedPassword && (
            <button type="button" onClick={onClose}>
              {t('auth.reset_password.cancel')}
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
