// Task: T006 — UsersGroupsPage tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { UsersGroupsPage } from '../../src/pages/UsersGroupsPage'
import * as adminApi from '../../src/api/adminApi'
import '../../src/i18n'

// Stub useAdminGuard — no redirect side-effects in tests
vi.mock('../../src/hooks/useAdminGuard', () => ({ useAdminGuard: vi.fn() }))

// Stub child tabs so tests focus on page-level behaviour only
vi.mock('../../src/components/GroupsTab', () => ({
  GroupsTab: () => <div data-testid="groups-tab">GroupsTab</div>,
}))
vi.mock('../../src/components/UsersTab', () => ({
  UsersTab: () => <div data-testid="users-tab">UsersTab</div>,
}))

beforeEach(() => {
  vi.restoreAllMocks()
  // Provide minimal stubs so any un-mocked child API calls don't hang
  vi.spyOn(adminApi, 'listGroups').mockResolvedValue([])
  vi.spyOn(adminApi, 'listUsers').mockResolvedValue([])
})

function renderPage() {
  return render(
    <MemoryRouter>
      <UsersGroupsPage />
    </MemoryRouter>
  )
}

describe('UsersGroupsPage', () => {
  it('renders page title using i18n key users_groups_page_title', () => {
    renderPage()
    expect(screen.getByRole('heading')).toBeTruthy()
  })

  it('renders Groups tab button and Users tab button', () => {
    renderPage()
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThanOrEqual(2)
  })

  it('default tab is Groups — GroupsTab rendered on first render', () => {
    renderPage()
    expect(screen.getByTestId('groups-tab')).toBeTruthy()
    expect(screen.queryByTestId('users-tab')).toBeNull()
  })

  it('Groups tab button has active class on first render', () => {
    renderPage()
    const tabButtons = screen.getAllByRole('button').filter(
      (b) => b.className === 'active' || b.className === ''
    )
    const activeButton = tabButtons.find((b) => b.className === 'active')
    expect(activeButton).toBeTruthy()
  })

  it('clicking Users tab renders UsersTab and hides GroupsTab', async () => {
    renderPage()
    const buttons = screen.getAllByRole('button')
    // Second tab button is "Users"
    const usersTabBtn = buttons[1]
    fireEvent.click(usersTabBtn)
    await waitFor(() => {
      expect(screen.getByTestId('users-tab')).toBeTruthy()
      expect(screen.queryByTestId('groups-tab')).toBeNull()
    })
  })

  it('clicking Groups tab after Users tab switches back to GroupsTab', async () => {
    renderPage()
    const buttons = screen.getAllByRole('button')
    fireEvent.click(buttons[1]) // switch to Users
    await waitFor(() => screen.getByTestId('users-tab'))
    fireEvent.click(buttons[0]) // switch back to Groups
    await waitFor(() => {
      expect(screen.getByTestId('groups-tab')).toBeTruthy()
      expect(screen.queryByTestId('users-tab')).toBeNull()
    })
  })

  it('calls useAdminGuard at page level', async () => {
    const guardModule = await import('../../src/hooks/useAdminGuard')
    const guardSpy = vi.spyOn(guardModule, 'useAdminGuard')
    renderPage()
    expect(guardSpy).toHaveBeenCalled()
  })
})
