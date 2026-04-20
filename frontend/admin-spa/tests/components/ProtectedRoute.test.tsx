import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '../../src/components/auth/ProtectedRoute'
import { useAuthStore } from '../../src/store/authStore'

beforeEach(() => {
  useAuthStore.setState({
    token: null,
    username: null,
    isAdmin: false,
    sessionExpiredMessage: null,
    _refreshTimer: null,
  })
})

function renderWithRouter(initialEntry = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <div>Dashboard Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('token=null → redirects to /login', () => {
    renderWithRouter()
    expect(screen.getByText('Login Page')).toBeInTheDocument()
    expect(screen.queryByText('Dashboard Content')).not.toBeInTheDocument()
  })

  it('token set + isAdmin=false → redirects to /login', () => {
    useAuthStore.setState({ token: 'tok', username: 'u', isAdmin: false, sessionExpiredMessage: null, _refreshTimer: null })
    renderWithRouter()
    expect(screen.getByText('Login Page')).toBeInTheDocument()
    expect(screen.queryByText('Dashboard Content')).not.toBeInTheDocument()
  })

  it('token + isAdmin=true → renders children', () => {
    useAuthStore.setState({ token: 'tok', username: 'admin', isAdmin: true, sessionExpiredMessage: null, _refreshTimer: null })
    renderWithRouter()
    expect(screen.getByText('Dashboard Content')).toBeInTheDocument()
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
  })
})
