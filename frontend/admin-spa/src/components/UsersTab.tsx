// Spec: docs/admin-spa/spec/admin-spa.spec.md#S003
// Task: T005 — UsersTab — users table + search (debounced 300ms) + assign groups + toggle active
import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import type { GroupItem, UserItem } from '../api/adminApi'
import { listGroups, listUsers, toggleUserActive } from '../api/adminApi'
import { AssignGroupModal } from './AssignGroupModal'

interface ToastState {
  msg: string
  type: 'success' | 'error'
}

export function UsersTab() {
  const { t } = useTranslation()

  const [search, setSearch] = useState('')
  const [users, setUsers] = useState<UserItem[]>([])
  const [allGroups, setAllGroups] = useState<GroupItem[]>([])
  const [loading, setLoading] = useState(true)
  const [assignTarget, setAssignTarget] = useState<UserItem | null>(null)
  const [toast, setToast] = useState<ToastState | null>(null)

  const loadUsers = useCallback(async (q: string) => {
    setLoading(true)
    try {
      const data = await listUsers(q || undefined)
      setUsers(data)
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load: groups only; debounce effect below covers initial users fetch
  useEffect(() => {
    listGroups().then(setAllGroups).catch(() => {
      setToast({ msg: t('group_delete_error'), type: 'error' })
    })
  }, [t])

  // Debounce search 300ms — also handles initial load (search='')
  useEffect(() => {
    const id = setTimeout(() => loadUsers(search), 300)
    return () => clearTimeout(id)
  }, [search, loadUsers])

  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(null), 3000)
    return () => clearTimeout(timer)
  }, [toast])

  async function handleToggleActive(user: UserItem) {
    try {
      await toggleUserActive(user.id, !user.is_active)
      await loadUsers(search)
    } catch {
      setToast({ msg: t('toggle_active_error'), type: 'error' })
    }
  }

  function handleAssignClose() {
    setAssignTarget(null)
  }

  async function handleAssignSave() {
    setAssignTarget(null)
    await loadUsers(search)
  }

  return (
    <div className="users-tab">
      <input
        type="text"
        className="search-input"
        placeholder={t('users_search_placeholder')}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {loading ? (
        <div className="loading-state" />
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t('col_email')}</th>
              <th>{t('col_groups')}</th>
              <th>{t('col_active')}</th>
              <th>{t('col_actions')}</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.email}</td>
                <td>
                  {user.groups.map((g) => (
                    <span key={g.id} className="badge-member" style={{ marginRight: '0.25rem' }}>
                      {g.name}
                    </span>
                  ))}
                </td>
                <td>
                  {user.is_active ? (
                    <span className="badge-active">{t('badge_active')}</span>
                  ) : (
                    <span className="badge-inactive">{t('badge_inactive')}</span>
                  )}
                </td>
                <td>
                  <button
                    className="btn-secondary"
                    onClick={() => setAssignTarget(user)}
                  >
                    {t('btn_assign_groups')}
                  </button>
                  {' '}
                  <button
                    className="btn-secondary"
                    onClick={() => handleToggleActive(user)}
                  >
                    {t('btn_toggle_active')}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {assignTarget && (
        <AssignGroupModal
          user={assignTarget}
          allGroups={allGroups}
          onSave={handleAssignSave}
          onClose={handleAssignClose}
        />
      )}

      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.msg}</div>
      )}
    </div>
  )
}
