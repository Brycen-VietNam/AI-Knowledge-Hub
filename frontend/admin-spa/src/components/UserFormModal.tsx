// Spec: docs/user-management/spec/user-management.spec.md#S006
// Task: S006 T001/T002/T003 — UserFormModal — create user with groups, generate-password, error handling
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { GroupItem, UserItem, UserCreatePayload } from '../api/adminApi'
import { createUser } from '../api/adminApi'

interface Props {
  onSave: (user: UserItem) => void
  onClose: () => void
  groups: GroupItem[]
}

const CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

function generatePassword(): string {
  const arr = crypto.getRandomValues(new Uint8Array(16))
  return Array.from(arr)
    .map((b) => CHARSET[b % CHARSET.length])
    .join('')
}

export function UserFormModal({ onSave, onClose, groups }: Props) {
  const { t } = useTranslation()

  const [sub, setSub] = useState('')
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [selectedGroupIds, setSelectedGroupIds] = useState<number[]>([])
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  function handleGroupToggle(groupId: number) {
    setSelectedGroupIds((prev) =>
      prev.includes(groupId) ? prev.filter((id) => id !== groupId) : [...prev, groupId],
    )
  }

  function handleGenerate() {
    const pwd = generatePassword()
    setPassword(pwd)
    setShowPassword(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      const payload: UserCreatePayload = {
        sub: sub.trim(),
        password,
        ...(email.trim() ? { email: email.trim() } : {}),
        ...(displayName.trim() ? { display_name: displayName.trim() } : {}),
        ...(selectedGroupIds.length > 0 ? { group_ids: selectedGroupIds } : {}),
      }
      const result = await createUser(payload)
      onSave(result)
      onClose()
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { status?: number; data?: { detail?: Array<{ loc: string[]; msg: string }> | string; message?: string } }
      }
      if (axiosErr.response?.status === 409) {
        setError(t('user.create.error.duplicate_sub'))
      } else if (axiosErr.response?.status === 422) {
        const detail = axiosErr.response?.data?.detail
        if (Array.isArray(detail)) {
          const errs: Record<string, string> = {}
          detail.forEach((d) => { if (d.loc[1]) errs[d.loc[1]] = d.msg })
          setFieldErrors(errs)
        } else {
          setError(typeof detail === 'string' ? detail : t('common.error.unexpected'))
        }
      } else {
        setError(t('common.error.unexpected'))
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="confirm-dialog-overlay" onClick={() => { if (!isSubmitting) onClose() }}>
      <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
        <h2>{t('user.create.title')}</h2>
        <form onSubmit={handleSubmit} className="upload-form">
          {/* sub */}
          <div className="upload-field">
            <label>{t('user.form.sub_label')}</label>
            <input
              type="text"
              value={sub}
              required
              pattern="[a-zA-Z0-9_.@\-]+"
              onChange={(e) => setSub(e.target.value)}
              disabled={isSubmitting}
              autoComplete="off"
            />
            {fieldErrors.sub && <p className="field-error">{fieldErrors.sub}</p>}
            <p className="field-hint">{t('user.form.hint_sub')}</p>
          </div>

          {/* email */}
          <div className="upload-field">
            <label>{t('user.form.email_label')}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
              autoComplete="off"
            />
            {fieldErrors.email && <p className="field-error">{fieldErrors.email}</p>}
            <p className="field-hint">{t('user.form.hint_email')}</p>
          </div>

          {/* display_name */}
          <div className="upload-field">
            <label>{t('user.form.display_name_label')}</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          {/* password */}
          <div className="upload-field">
            <label>{t('user.form.password_label')}</label>
            <div className="password-field-row">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                minLength={12}
                required
                onChange={(e) => setPassword(e.target.value)}
                disabled={isSubmitting}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowPassword((v) => !v)}
                disabled={isSubmitting}
              >
                {showPassword ? t('user.form.hide_password') : t('user.form.show_password')}
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleGenerate}
                disabled={isSubmitting}
              >
                {t('user.form.generate_password')}
              </button>
            </div>
            {fieldErrors.password && <p className="field-error">{fieldErrors.password}</p>}
            <p className="field-hint">{t('user.form.hint_password')}</p>
          </div>

          {/* groups */}
          {groups.length > 0 && (
            <div className="upload-field">
              <label>{t('user.form.groups_label')}</label>
              {groups.map((g) => (
                <label key={g.id} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedGroupIds.includes(g.id)}
                    onChange={() => handleGroupToggle(g.id)}
                    disabled={isSubmitting}
                  />
                  {' '}{g.name}
                </label>
              ))}
            </div>
          )}

          {error && <p className="form-error">{error}</p>}

          <div className="upload-modal-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              {t('btn_cancel')}
            </button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {t('btn_save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
