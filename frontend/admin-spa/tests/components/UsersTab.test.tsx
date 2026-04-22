// Task: T005 — UsersTab tests
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { UsersTab } from '../../src/components/UsersTab'
import * as adminApi from '../../src/api/adminApi'
import '../../src/i18n'

const ALL_GROUPS: adminApi.GroupItem[] = [
  { id: 1, name: 'editors', is_admin: false, member_count: 3 },
  { id: 2, name: 'viewers', is_admin: false, member_count: 5 },
]

const USERS: adminApi.UserItem[] = [
  {
    id: 'u1',
    email: 'alice@example.com',
    is_active: true,
    has_password: true,
    groups: [{ id: 1, name: 'editors' }],
  },
  {
    id: 'u2',
    email: 'bob@example.com',
    is_active: false,
    has_password: false,
    groups: [],
  },
]

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('UsersTab', () => {
  it('renders users table after load', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    render(<UsersTab />)
    await waitFor(() => {
      expect(screen.getByText('alice@example.com')).toBeTruthy()
      expect(screen.getByText('bob@example.com')).toBeTruthy()
    })
  })

  it('shows active badge for active user and inactive badge for inactive user', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    render(<UsersTab />)
    await waitFor(() => {
      expect(document.querySelector('.badge-active')).toBeTruthy()
      expect(document.querySelector('.badge-inactive')).toBeTruthy()
    })
  })

  it('search debounces 300ms — not called on every keystroke', async () => {
    vi.useFakeTimers()
    try {
      vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
      const listUsersSpy = vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
      // Render and flush initial promises (effect 1: loadUsers(''))
      await act(async () => {
        render(<UsersTab />)
      })
      // Advance 300ms to allow debounce effect on mount to also fire
      await act(async () => {
        vi.advanceTimersByTime(300)
      })
      const callsAfterMount = listUsersSpy.mock.calls.length

      const searchInput = document.querySelector('input[type="text"]') as HTMLInputElement
      // Type quickly — multiple changes before 300ms
      fireEvent.change(searchInput, { target: { value: 'a' } })
      fireEvent.change(searchInput, { target: { value: 'al' } })
      fireEvent.change(searchInput, { target: { value: 'ali' } })
      // No extra API call yet (debounce pending)
      expect(listUsersSpy.mock.calls.length).toBe(callsAfterMount)
      // Advance 300ms — debounce fires exactly once with final value
      await act(async () => {
        vi.advanceTimersByTime(300)
      })
      expect(listUsersSpy.mock.calls.length).toBe(callsAfterMount + 1)
      expect(listUsersSpy).toHaveBeenLastCalledWith('ali')
    } finally {
      vi.useRealTimers()
    }
  })

  it('opens AssignGroupModal when Assign Groups button is clicked', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    const assignButtons = screen.getAllByRole('button', { name: /assign/i })
    fireEvent.click(assignButtons[0])
    await waitFor(() => {
      expect(document.querySelector('.upload-modal')).toBeTruthy()
    })
  })

  it('AssignGroupModal receives allGroups fetched from listGroups', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    const assignButtons = screen.getAllByRole('button', { name: /assign/i })
    fireEvent.click(assignButtons[0])
    await waitFor(() => {
      // 'editors' appears in both the table badge and the modal checkbox — use getAllByText
      expect(screen.getAllByText('editors').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('viewers').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('calls toggleUserActive when Toggle Active button is clicked', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    const toggleSpy = vi.spyOn(adminApi, 'toggleUserActive').mockResolvedValue(undefined)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    const toggleButtons = screen.getAllByRole('button', { name: /toggle/i })
    fireEvent.click(toggleButtons[0])
    await waitFor(() => {
      expect(toggleSpy).toHaveBeenCalledWith('u1', false)
    })
  })

  it('reloads users after assign save', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    const listUsersSpy = vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    vi.spyOn(adminApi, 'assignGroups').mockResolvedValue(undefined)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    const callsBeforeAssign = listUsersSpy.mock.calls.length
    const assignButtons = screen.getAllByRole('button', { name: /assign/i })
    fireEvent.click(assignButtons[0])
    await waitFor(() => document.querySelector('.upload-modal'))
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(listUsersSpy.mock.calls.length).toBeGreaterThan(callsBeforeAssign)
    })
  })

  // ── S008: Create User ─────────────────────────────────────────────────────

  it('create button opens UserFormModal', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    fireEvent.click(screen.getByText('Create User'))
    await waitFor(() => {
      expect(document.querySelector('.upload-modal')).toBeTruthy()
    })
  })

  it('onSave closes modal and prepends new user to list', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    const newUser: adminApi.UserItem = { id: 'u99', email: 'new@example.com', is_active: true, has_password: true, groups: [] }
    vi.spyOn(adminApi, 'createUser').mockResolvedValue(newUser)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    fireEvent.click(screen.getByText('Create User'))
    await waitFor(() => expect(document.querySelector('.upload-modal')).toBeTruthy())
    // Fill required fields in UserFormModal
    const subInput = document.querySelector('input[pattern]') as HTMLInputElement
    fireEvent.change(subInput, { target: { value: 'newuser' } })
    const pwInput = document.querySelector('input[type="password"]') as HTMLInputElement
    fireEvent.change(pwInput, { target: { value: 'StrongPass1234' } })
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(document.querySelector('.upload-modal')).toBeNull()
      expect(screen.getByText('new@example.com')).toBeTruthy()
    })
  })

  // ── S008: Delete User ─────────────────────────────────────────────────────

  it('delete button opens DeleteConfirmDialog', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    await waitFor(() => {
      expect(document.querySelector('.confirm-dialog')).toBeTruthy()
    })
  })

  it('confirm delete removes user from list', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    vi.spyOn(adminApi, 'deleteUser').mockResolvedValue()
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    await waitFor(() => expect(document.querySelector('.confirm-dialog')).toBeTruthy())
    fireEvent.click(document.querySelector('.confirm-dialog .btn-danger')!)
    await waitFor(() => {
      expect(screen.queryByText('alice@example.com')).toBeNull()
      expect(screen.getByText('bob@example.com')).toBeTruthy()
    })
  })

  it('delete error shows toast and row stays in list', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    vi.spyOn(adminApi, 'deleteUser').mockRejectedValue(new Error('404'))
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    await waitFor(() => expect(document.querySelector('.confirm-dialog')).toBeTruthy())
    fireEvent.click(document.querySelector('.confirm-dialog .btn-danger')!)
    await waitFor(() => {
      expect(document.querySelector('.toast-error')).toBeTruthy()
      expect(screen.getByText('alice@example.com')).toBeTruthy()
    })
  })

  // ── S008: ApiKeyPanel expand/collapse ─────────────────────────────────────

  it('clicking email cell expands ApiKeyPanel for that user', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue([])
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    fireEvent.click(screen.getByText('alice@example.com'))
    await waitFor(() => {
      expect(document.querySelector('.api-key-panel')).toBeTruthy()
    })
    expect(adminApi.listApiKeys).toHaveBeenCalledWith('u1')
  })

  it('clicking same email again collapses ApiKeyPanel', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue([])
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    fireEvent.click(screen.getByText('alice@example.com'))
    await waitFor(() => expect(document.querySelector('.api-key-panel')).toBeTruthy())
    fireEvent.click(screen.getByText('alice@example.com'))
    await waitFor(() => {
      expect(document.querySelector('.api-key-panel')).toBeNull()
    })
  })

  // ── S004 change-password: Reset Password button ───────────────────────────

  it('shows Reset Password button only for users with has_password=true', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    // alice has_password=true → button shown; bob has_password=false → button hidden
    const resetButtons = screen.getAllByText('Reset Password')
    expect(resetButtons).toHaveLength(1)
  })

  it('opens ResetPasswordModal when Reset Password button is clicked', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    fireEvent.click(screen.getByText('Reset Password'))
    await waitFor(() => {
      expect(document.querySelector('.reset-password-modal')).toBeTruthy()
    })
  })

  it('toggle-active regression — still works after S008 wiring', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(ALL_GROUPS)
    vi.spyOn(adminApi, 'listUsers').mockResolvedValue(USERS)
    const toggleSpy = vi.spyOn(adminApi, 'toggleUserActive').mockResolvedValue(undefined)
    render(<UsersTab />)
    await waitFor(() => screen.getByText('alice@example.com'))
    const toggleButtons = screen.getAllByRole('button', { name: /toggle/i })
    fireEvent.click(toggleButtons[0])
    await waitFor(() => {
      expect(toggleSpy).toHaveBeenCalledWith('u1', false)
    })
  })
})
