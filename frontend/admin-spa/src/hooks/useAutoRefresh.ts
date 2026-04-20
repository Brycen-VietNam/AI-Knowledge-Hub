// Spec: docs/admin-spa/spec/admin-spa.spec.md#S004
// Task: T003 (S004) — useAutoRefresh hook (AC6: auto-refresh every 60s)
import { useEffect } from 'react'

export function useAutoRefresh(fn: () => void, intervalMs = 60_000): void {
  useEffect(() => {
    fn()
    const id = setInterval(fn, intervalMs)
    return () => clearInterval(id)
  }, [fn, intervalMs])
}
