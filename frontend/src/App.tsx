// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Task: T005 — App.tsx — Router + ProtectedRoute; setNavigate wired once at mount
// Decision: T003 analysis — setNavigate called in useEffect to guarantee Router context exists
import { useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { setNavigate } from './api/client'
import { LoginPage } from './pages/LoginPage'
import { QueryPage } from './pages/QueryPage'
import { ProtectedRoute } from './components/auth/ProtectedRoute'

function App() {
  const navigate = useNavigate()

  useEffect(() => {
    setNavigate(navigate)
  }, [navigate])

  return (
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
  )
}

export default App
