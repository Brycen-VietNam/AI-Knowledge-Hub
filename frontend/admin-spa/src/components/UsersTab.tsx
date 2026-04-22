// Spec: docs/admin-spa/spec/admin-spa.spec.md#S003
// Task: T005 — UsersTab — users table + search (debounced 300ms) + assign groups + toggle active
// Task: S008 T001–T004 — create user, delete user, ApiKeyPanel expand/collapse
// Task: change-password/S004 — Reset Password button per non-OIDC row
import { useState, useEffect, useCallback, Fragment } from 'react'
import { useTranslation } from 'react-i18next'
import type { GroupItem, UserItem } from '../api/adminApi'
import { listGroups, listUsers, toggleUserActive, deleteUser } from '../api/adminApi'
import { AssignGroupModal } from './AssignGroupModal'
import { DeleteConfirmDialog } from './DeleteConfirmDialog'
import { UserFormModal } from './UserFormModal'
import { ApiKeyPanel } from './ApiKeyPanel'
import { ResetPasswordModal } from './ResetPasswordModal'

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

  // S008: new state — create modal, expand, delete confirm
  const [modalMode, setModalMode] = useState<null | 'create'>(null)
  const [expandedUserId, setExpandedUserId] = useState<string | null>(null)
  const [deletingUserId, setDeletingUserId] = useState<string | null>(null)
  const [resetPasswordUserId, setResetPasswordUserId] = useState<string | null>(null)

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

  async function handleDeleteConfirm() {
    if (!deletingUserId) return
    try {
      await deleteUser(deletingUserId)
      setUsers((prev) => prev.filter((u) => u.id !== deletingUserId))
      setDeletingUserId(null)
    } catch {
      setToast({ msg: t('user_delete_error'), type: 'error' })
      setDeletingUserId(null)
    }
  }

  function handleExpandToggle(userId: string) {
    setExpandedUserId((prev) => (prev === userId ? null : userId))
  }

  return (
    <div className="users-tab">
      <div className="tab-toolbar">
        <button className="btn-primary" onClick={() => setModalMode('create')}>
          {t('btn_create_user')}
        </button>
      </div>

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
              <Fragment key={user.id}>
                <tr>
                  <td style={{ cursor: 'pointer' }} onClick={() => handleExpandToggle(user.id)}>
                    {user.email}
                  </td>
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
                    {' '}
                    {user.has_password && (
                      <>
                        {' '}
                        <button
                          className="btn-secondary"
                          onClick={() => setResetPasswordUserId(user.id)}
                        >
                          {t('btn_reset_password')}
                        </button>
                      </>
                    )}
                    {' '}
                    <button
                      className="btn-danger"
                      onClick={() => setDeletingUserId(user.id)}
                    >
                      {t('btn_delete')}
                    </button>
                  </td>
                </tr>
                {expandedUserId === user.id && (
                  <tr>
                    <td colSpan={4}>
                      <ApiKeyPanel userId={user.id} />
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}

      {modalMode === 'create' && (
        <UserFormModal
          groups={allGroups}
          onSave={(user) => { setUsers((prev) => [user, ...prev]); setModalMode(null) }}
          onClose={() => setModalMode(null)}
        />
      )}

      {assignTarget && (
        <AssignGroupModal
          user={assignTarget}
          allGroups={allGroups}
          onSave={handleAssignSave}
          onClose={handleAssignClose}
        />
      )}

      <DeleteConfirmDialog
        open={deletingUserId !== null}
        title={t('user_delete_title')}
        message={t('user_delete_message')}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeletingUserId(null)}
      />

      {resetPasswordUserId && (
        <ResetPasswordModal
          userId={resetPasswordUserId}
          onClose={() => setResetPasswordUserId(null)}
        />
      )}

      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.msg}</div>
      )}
    </div>
  )
}
