// Spec: docs/admin-spa/spec/admin-spa.spec.md#S003
// Task: T002 — GroupFormModal — create/edit group modal
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { GroupItem } from '../api/adminApi'
import { createGroup, updateGroup } from '../api/adminApi'

interface Props {
  mode: 'create' | 'edit'
  initial?: GroupItem
  onSave: (name: string, isAdmin: boolean) => void
  onClose: () => void
}

export function GroupFormModal({ mode, initial, onSave, onClose }: Props) {
  const { t } = useTranslation()

  const [name, setName] = useState(initial?.name ?? '')
  const [isAdmin, setIsAdmin] = useState(initial?.is_admin ?? false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) {
      setError(t('group_save_error'))
      return
    }
    if (name.trim().length > 100) {
      setError(t('group_save_error'))
      return
    }
    setLoading(true)
    setError(null)
    try {
      if (mode === 'create') {
        await createGroup(name.trim(), isAdmin)
      } else {
        await updateGroup(initial!.id, name.trim(), isAdmin)
      }
      onSave(name.trim(), isAdmin)
      onClose()
    } catch {
      setError(t('group_save_error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="confirm-dialog-overlay" onClick={() => { if (!loading) onClose() }}>
      <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
        <h2>{mode === 'create' ? t('btn_create_group') : t('btn_edit')}</h2>
        <form onSubmit={handleSubmit}>
          <div className="upload-field">
            <label>{t('col_name')}</label>
            <input
              type="text"
              value={name}
              maxLength={100}
              onChange={(e) => setName(e.target.value)}
              disabled={loading}
            />
          </div>
          <div className="upload-field">
            <label>
              <input
                type="checkbox"
                checked={isAdmin}
                onChange={(e) => setIsAdmin(e.target.checked)}
                disabled={loading}
              />
              {' '}{t('group_is_admin_label')}
            </label>
          </div>
          {error && <div className="upload-error">{error}</div>}
          <div className="upload-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
              {t('btn_cancel')}
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {t('btn_save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
