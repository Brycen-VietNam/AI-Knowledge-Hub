// Task: T004 — GroupsTab tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { GroupsTab } from '../../src/components/GroupsTab'
import * as adminApi from '../../src/api/adminApi'
import '../../src/i18n'

const GROUPS: adminApi.GroupItem[] = [
  { id: 1, name: 'editors', is_admin: false, member_count: 3 },
  { id: 2, name: 'admins', is_admin: true, member_count: 1 },
]

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('GroupsTab', () => {
  it('renders loading state initially', () => {
    vi.spyOn(adminApi, 'listGroups').mockReturnValue(new Promise(() => {}))
    render(<GroupsTab />)
    expect(document.querySelector('.loading-state')).toBeTruthy()
  })

  it('renders groups table after load', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(GROUPS)
    render(<GroupsTab />)
    await waitFor(() => {
      expect(screen.getByText('editors')).toBeTruthy()
      expect(screen.getByText('admins')).toBeTruthy()
    })
  })

  it('shows badge_admin for is_admin=true group', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(GROUPS)
    render(<GroupsTab />)
    await waitFor(() => {
      const adminBadge = document.querySelector('.badge-admin')
      expect(adminBadge).toBeTruthy()
    })
  })

  it('shows badge_member for is_admin=false group', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(GROUPS)
    render(<GroupsTab />)
    await waitFor(() => {
      const memberBadge = document.querySelector('.badge-member')
      expect(memberBadge).toBeTruthy()
    })
  })

  it('shows empty state when groups list is empty', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue([])
    render(<GroupsTab />)
    await waitFor(() => {
      expect(document.querySelector('.empty-state')).toBeTruthy()
    })
  })

  it('opens GroupFormModal when Create button is clicked', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(GROUPS)
    render(<GroupsTab />)
    await waitFor(() => screen.getByText('editors'))
    fireEvent.click(document.querySelector('.btn-primary')!)
    await waitFor(() => {
      expect(document.querySelector('.upload-modal')).toBeTruthy()
    })
  })

  it('reloads list after modal save', async () => {
    const listSpy = vi.spyOn(adminApi, 'listGroups').mockResolvedValue(GROUPS)
    vi.spyOn(adminApi, 'createGroup').mockResolvedValue({
      id: 3, name: 'writers', is_admin: false, member_count: 0,
    })
    render(<GroupsTab />)
    await waitFor(() => screen.getByText('editors'))
    // Open create modal
    const buttons = screen.getAllByRole('button')
    const createBtn = buttons.find((b) => b.className.includes('btn-primary'))!
    fireEvent.click(createBtn)
    await waitFor(() => document.querySelector('.upload-modal'))
    // Fill and submit
    const nameInput = document.querySelector('input[type="text"]') as HTMLInputElement
    fireEvent.change(nameInput, { target: { value: 'writers' } })
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(listSpy).toHaveBeenCalledTimes(2)
    })
  })

  it('calls deleteGroup when Delete button is clicked', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(GROUPS)
    const deleteSpy = vi.spyOn(adminApi, 'deleteGroup').mockResolvedValue(undefined)
    render(<GroupsTab />)
    await waitFor(() => screen.getByText('editors'))
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    fireEvent.click(deleteButtons[0])
    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalledOnce()
    })
  })

  it('shows conflict toast on 409 delete error', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(GROUPS)
    vi.spyOn(adminApi, 'deleteGroup').mockRejectedValue({ response: { status: 409 } })
    render(<GroupsTab />)
    await waitFor(() => screen.getByText('editors'))
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    fireEvent.click(deleteButtons[0])
    await waitFor(() => {
      expect(document.querySelector('.toast-error')).toBeTruthy()
    })
  })

  it('shows generic error toast on non-409 delete error', async () => {
    vi.spyOn(adminApi, 'listGroups').mockResolvedValue(GROUPS)
    vi.spyOn(adminApi, 'deleteGroup').mockRejectedValue({ response: { status: 500 } })
    render(<GroupsTab />)
    await waitFor(() => screen.getByText('editors'))
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    fireEvent.click(deleteButtons[0])
    await waitFor(() => {
      expect(document.querySelector('.toast-error')).toBeTruthy()
    })
  })
})
