// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Task: T005 — App.tsx — Router + ProtectedRoute; setNavigate wired once at mount
// Task: S002/T002 — Add sticky header with logo, LanguageSelector, user pill
// Decision: T003 analysis — setNavigate called in useEffect to guarantee Router context exists
// Decision: D005 — Header on all pages; user pill hidden when token === null
// Decision: D006 — Logo: "Knowledge Hub" + "BRYSEN GROUP"
import { useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { setNavigate } from './api/client'
import { LoginPage } from './pages/LoginPage'
import { QueryPage } from './pages/QueryPage'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { useAuthStore } from './store/authStore'
import { LanguageSelector } from './components/query/LanguageSelector'

function App() {
  const navigate = useNavigate()
  const { token, username } = useAuthStore()

  useEffect(() => {
    setNavigate(navigate)
  }, [navigate])

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
            <div className="user-pill">
              <div className="avatar">{username?.charAt(0).toUpperCase() ?? '?'}</div>
              <span className="user-name">{username ?? ''}</span>
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
        <Route path="/" element={<Navigate to="/query" replace />} />
      </Routes>
    </>
  )
}

export default App
