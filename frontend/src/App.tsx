// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Task: T005 — App.tsx — Router + ProtectedRoute; setNavigate wired once at mount
// Task: S002/T002 — Add sticky header with logo, LanguageSelector, user pill
// Task: S003/T004 — Convert user pill to dropdown; ChangePasswordModal wired
// Decision: T003 analysis — setNavigate called in useEffect to guarantee Router context exists
// Decision: D005 — Header on all pages; user pill hidden when token === null
// Decision: D006 — Logo: "Knowledge Hub" + "BRYSEN GROUP"
// Decision: D3 — Hide "Change Password" for OIDC users (password === null)
import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { setNavigate } from './api/client'
import { LoginPage } from './pages/LoginPage'
import { QueryPage } from './pages/QueryPage'
import { ChangePasswordPage } from './pages/ChangePasswordPage'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { ChangePasswordModal } from './components/auth/ChangePasswordModal'
import { useAuthStore } from './store/authStore'
import { LanguageSelector } from './components/query/LanguageSelector'

function App() {
  const navigate = useNavigate()
  const { token, username, refreshToken, logout } = useAuthStore()

  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [changePasswordOpen, setChangePasswordOpen] = useState(false)

  // Derived: local users have a refresh token; OIDC users do not (D3, D-SA-02)
  const hasPassword = refreshToken !== null

  useEffect(() => {
    setNavigate(navigate)
  }, [navigate])

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!dropdownOpen) return
    function handleClick() { setDropdownOpen(false) }
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [dropdownOpen])

  return (
    <>
      <header className="app-header">
        <div className="logo">
          <div className="logo-icon">✦</div>
          <div className="logo-text">
            <span className="logo-title">Knowledge Hub</span>
            <span className="logo-sub">BRYSEN GROUP</span>
          </div>
        </div>
        <div className="header-sep" />
        <LanguageSelector />
        {token !== null && (
          <>
            <div className="header-divider" />
            <div className="user-pill-dropdown">
              <button
                className="user-pill user-pill-btn"
                onClick={(e) => { e.stopPropagation(); setDropdownOpen((o) => !o) }}
                aria-haspopup="true"
                aria-expanded={dropdownOpen}
              >
                <div className="avatar">{username?.charAt(0).toUpperCase() ?? '?'}</div>
                <span className="user-name">{username ?? ''}</span>
              </button>
              {dropdownOpen && (
                <div className="user-pill-menu" role="menu">
                  {hasPassword && (
                    <button
                      className="user-pill-menu-item"
                      role="menuitem"
                      onClick={() => { setDropdownOpen(false); setChangePasswordOpen(true) }}
                    >
                      Change Password
                    </button>
                  )}
                  <button
                    className="user-pill-menu-item user-pill-menu-item--danger"
                    role="menuitem"
                    onClick={() => { setDropdownOpen(false); logout() }}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </header>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/query"
          element={
            <ProtectedRoute>
              <QueryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/change-password"
          element={
            <ProtectedRoute>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/query" replace />} />
      </Routes>
      {changePasswordOpen && (
        <ChangePasswordModal onClose={() => setChangePasswordOpen(false)} />
      )}
    </>
  )
}

export default App
