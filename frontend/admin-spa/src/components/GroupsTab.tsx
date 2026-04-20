// Spec: docs/admin-spa/spec/admin-spa.spec.md#S003
// Task: T004 — GroupsTab — groups CRUD table
import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import type { GroupItem } from '../api/adminApi'
import { listGroups, deleteGroup } from '../api/adminApi'
import { GroupFormModal } from './GroupFormModal'

interface ToastState {
  msg: string
  type: 'success' | 'error'
}

export function GroupsTab() {
  const { t } = useTranslation()

  const [groups, setGroups] = useState<GroupItem[]>([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState<ToastState | null>(null)
  const [modalMode, setModalMode] = useState<'create' | 'edit' | null>(null)
  const [editTarget, setEditTarget] = useState<GroupItem | null>(null)

  const loadGroups = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listGroups()
      setGroups(data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadGroups()
  }, [loadGroups])

  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(null), 3000)
    return () => clearTimeout(timer)
  }, [toast])

  async function handleDelete(id: number) {
    try {
      await deleteGroup(id)
      await loadGroups()
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 409) {
        setToast({ msg: t('group_delete_conflict'), type: 'error' })
      } else {
        setToast({ msg: t('group_delete_error'), type: 'error' })
      }
    }
  }

  function handleCreate() {
    setEditTarget(null)
    setModalMode('create')
  }

  function handleEdit(group: GroupItem) {
    setEditTarget(group)
    setModalMode('edit')
  }

  function handleModalClose() {
    setModalMode(null)
    setEditTarget(null)
  }

  async function handleModalSave() {
    setModalMode(null)
    setEditTarget(null)
    await loadGroups()
  }

  return (
    <div className="groups-tab">
      <div className="tab-toolbar">
        <button className="btn-primary" onClick={handleCreate}>
          {t('btn_create_group')}
        </button>
      </div>

      {loading ? (
        <div className="loading-state" />
      ) : groups.length === 0 ? (
        <div className="empty-state">{t('groups_empty')}</div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t('col_name')}</th>
              <th>{t('col_type')}</th>
              <th>{t('col_members')}</th>
              <th>{t('col_actions')}</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((group) => (
              <tr key={group.id}>
                <td>{group.name}</td>
                <td>
                  {group.is_admin ? (
                    <span className="badge-admin">{t('badge_admin')}</span>
                  ) : (
                    <span className="badge-member">{t('badge_member')}</span>
                  )}
                </td>
                <td>{group.member_count}</td>
                <td>
                  <button
                    className="btn-secondary"
                    onClick={() => handleEdit(group)}
                  >
                    {t('btn_edit')}
                  </button>
                  {' '}
                  <button
                    className="btn-danger"
                    onClick={() => handleDelete(group.id)}
                  >
                    {t('btn_delete')}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {modalMode !== null && (
        <GroupFormModal
          mode={modalMode}
          initial={editTarget ?? undefined}
          onSave={handleModalSave}
          onClose={handleModalClose}
        />
      )}

      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.msg}</div>
      )}
    </div>
  )
}
