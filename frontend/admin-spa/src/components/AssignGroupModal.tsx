// Spec: docs/admin-spa/spec/admin-spa.spec.md#S003
// Task: T003 — AssignGroupModal — multi-select groups for user
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { GroupItem, UserItem } from '../api/adminApi'
import { assignGroups } from '../api/adminApi'

interface Props {
  user: UserItem
  allGroups: GroupItem[]
  onSave: (groupIds: number[]) => void
  onClose: () => void
}

export function AssignGroupModal({ user, allGroups, onSave, onClose }: Props) {
  const { t } = useTranslation()

  const [selected, setSelected] = useState<Set<number>>(
    new Set(user.groups.map((g) => g.id))
  )
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function toggle(id: number) {
    setSelected((prev) => {
      const s = new Set(prev)
      s.has(id) ? s.delete(id) : s.add(id)
      return s
    })
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await assignGroups(user.id, [...selected])
      onSave([...selected])
      onClose()
    } catch {
      setError(t('assign_groups_error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="confirm-dialog-overlay" onClick={() => { if (!loading) onClose() }}>
      <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
        <h2>{t('btn_assign_groups')}</h2>
        <form onSubmit={handleSave}>
          <div className="upload-field">
            {allGroups.map((group) => (
              <label key={group.id} style={{ display: 'block', marginBottom: '0.25rem' }}>
                <input
                  type="checkbox"
                  checked={selected.has(group.id)}
                  onChange={() => toggle(group.id)}
                  disabled={loading}
                />
                {' '}{group.name}
              </label>
            ))}
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
