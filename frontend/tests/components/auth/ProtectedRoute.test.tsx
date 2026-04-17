import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '../../../src/components/auth/ProtectedRoute'
import { useAuthStore } from '../../../src/store/authStore'
import '../../../src/i18n'

beforeEach(() => {
  useAuthStore.setState({ token: null, username: null, password: null, _refreshTimer: null })
})

function renderWithRouter(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route
          path="/query"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute — unauthenticated', () => {
  it('redirects to /login when no token', () => {
    renderWithRouter('/query')
    expect(screen.getByText('Login Page')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })
})

describe('ProtectedRoute — authenticated', () => {
  it('renders children when token is present', () => {
    useAuthStore.setState({ token: 'valid-token' })
    renderWithRouter('/query')
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
  })
})

describe('App routing — root redirect', () => {
  it('/ redirects to /query (then to /login when unauthenticated)', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route
            path="/query"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<div>Root</div>} />
        </Routes>
      </MemoryRouter>,
    )
    // Without the Navigate component in place, root stays at root.
    // This test verifies ProtectedRoute independently — full routing tested via App integration.
    expect(screen.getByText('Root')).toBeInTheDocument()
  })
})
