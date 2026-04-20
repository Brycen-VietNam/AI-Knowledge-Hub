// Task: T003 — AssignGroupModal tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AssignGroupModal } from '../../src/components/AssignGroupModal'
import * as adminApi from '../../src/api/adminApi'
import '../../src/i18n'

const ALL_GROUPS: adminApi.GroupItem[] = [
  { id: 1, name: 'editors', is_admin: false, member_count: 3 },
  { id: 2, name: 'viewers', is_admin: false, member_count: 5 },
  { id: 3, name: 'admins', is_admin: true, member_count: 1 },
]

const USER_WITH_GROUPS: adminApi.UserItem = {
  id: 'u1',
  email: 'alice@example.com',
  is_active: true,
  groups: [{ id: 1, name: 'editors' }],
}

const USER_NO_GROUPS: adminApi.UserItem = {
  id: 'u2',
  email: 'bob@example.com',
  is_active: true,
  groups: [],
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('AssignGroupModal', () => {
  it('renders all groups from allGroups', () => {
    render(
      <AssignGroupModal
        user={USER_WITH_GROUPS}
        allGroups={ALL_GROUPS}
        onSave={vi.fn()}
        onClose={vi.fn()}
      />
    )
    expect(screen.getByText('editors')).toBeTruthy()
    expect(screen.getByText('viewers')).toBeTruthy()
    expect(screen.getByText('admins')).toBeTruthy()
  })

  it('pre-selects user current groups on open', () => {
    render(
      <AssignGroupModal
        user={USER_WITH_GROUPS}
        allGroups={ALL_GROUPS}
        onSave={vi.fn()}
        onClose={vi.fn()}
      />
    )
    const checkboxes = document.querySelectorAll('input[type="checkbox"]') as NodeListOf<HTMLInputElement>
    // editors (id=1) checked, viewers (id=2) unchecked, admins (id=3) unchecked
    expect(checkboxes[0].checked).toBe(true)
    expect(checkboxes[1].checked).toBe(false)
    expect(checkboxes[2].checked).toBe(false)
  })

  it('renders all groups even when user has no groups', () => {
    render(
      <AssignGroupModal
        user={USER_NO_GROUPS}
        allGroups={ALL_GROUPS}
        onSave={vi.fn()}
        onClose={vi.fn()}
      />
    )
    const checkboxes = document.querySelectorAll('input[type="checkbox"]') as NodeListOf<HTMLInputElement>
    expect(checkboxes).toHaveLength(3)
    checkboxes.forEach((cb) => expect(cb.checked).toBe(false))
  })

  it('toggling checkbox updates selection', () => {
    render(
      <AssignGroupModal
        user={USER_WITH_GROUPS}
        allGroups={ALL_GROUPS}
        onSave={vi.fn()}
        onClose={vi.fn()}
      />
    )
    const checkboxes = document.querySelectorAll('input[type="checkbox"]') as NodeListOf<HTMLInputElement>
    // uncheck editors
    fireEvent.click(checkboxes[0])
    expect(checkboxes[0].checked).toBe(false)
    // check viewers
    fireEvent.click(checkboxes[1])
    expect(checkboxes[1].checked).toBe(true)
  })

  it('calls assignGroups with correct ids and onSave+onClose on success', async () => {
    vi.spyOn(adminApi, 'assignGroups').mockResolvedValue(undefined)
    const onSave = vi.fn()
    const onClose = vi.fn()
    render(
      <AssignGroupModal
        user={USER_WITH_GROUPS}
        allGroups={ALL_GROUPS}
        onSave={onSave}
        onClose={onClose}
      />
    )
    // also check viewers
    const checkboxes = document.querySelectorAll('input[type="checkbox"]') as NodeListOf<HTMLInputElement>
    fireEvent.click(checkboxes[1])
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(adminApi.assignGroups).toHaveBeenCalledWith('u1', expect.arrayContaining([1, 2]))
      expect(onSave).toHaveBeenCalledOnce()
      expect(onClose).toHaveBeenCalledOnce()
    })
  })

  it('shows inline error on API failure', async () => {
    vi.spyOn(adminApi, 'assignGroups').mockRejectedValue(new Error('network'))
    render(
      <AssignGroupModal
        user={USER_WITH_GROUPS}
        allGroups={ALL_GROUPS}
        onSave={vi.fn()}
        onClose={vi.fn()}
      />
    )
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(document.querySelector('.upload-error')).toBeTruthy()
    })
  })

  it('calls onClose when cancel button is clicked', () => {
    const onClose = vi.fn()
    render(
      <AssignGroupModal
        user={USER_WITH_GROUPS}
        allGroups={ALL_GROUPS}
        onSave={vi.fn()}
        onClose={onClose}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onClose).toHaveBeenCalledOnce()
  })
})
