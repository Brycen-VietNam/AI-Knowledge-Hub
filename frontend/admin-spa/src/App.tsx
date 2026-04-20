// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T008 — App.tsx — router + header + /login + /dashboard routes (AC5, AC6, AC7, AC8)
// Decision: setNavigate wired in useEffect; ProtectedRoute wraps /dashboard
import { useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { setNavigate } from './api/client'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { useAuthStore } from './store/authStore'
import { LanguageSelector } from './components/LanguageSelector'

function App() {
  const { t } = useTranslation()
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
            <span className="logo-title">{t('login.title')}</span>
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
            <button
              onClick={() => useAuthStore.getState().logout()}
              className="logout-btn"
            >
              {t('nav.logout')}
            </button>
          </>
        )}
      </header>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/documents"
          element={
            <ProtectedRoute>
              <DocumentsPage />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </>
  )
}

export default App
