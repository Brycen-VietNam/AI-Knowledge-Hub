// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T003 — Axios client — Bearer interceptor + 401 logout/redirect + sessionExpired
// Decision: baseURL from VITE_API_BASE_URL only (S005 — no hardcoded URLs)
import axios from 'axios'
import { useAuthStore } from '../store/authStore'

let _navigate: ((path: string) => void) | null = null

export function setNavigate(fn: (path: string) => void): void {
  _navigate = fn
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl: string = error.config?.url ?? ''
    if (error.response?.status === 401 && !requestUrl.includes('/v1/auth/token')) {
      useAuthStore.getState().setSessionExpired()
      useAuthStore.getState().logout()
      if (_navigate) {
        _navigate('/login')
      }
    }
    return Promise.reject(error)
  },
)
