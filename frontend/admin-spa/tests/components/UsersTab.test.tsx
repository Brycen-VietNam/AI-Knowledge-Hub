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
    groups: [{ id: 1, name: 'editors' }],
  },
  {
    id: 'u2',
    email: 'bob@example.com',
    is_active: false,
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
})
