// Task: T003 (S004) — useAutoRefresh hook tests
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useAutoRefresh } from '../../src/hooks/useAutoRefresh'

describe('useAutoRefresh', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('calls fn immediately on mount', () => {
    const fn = vi.fn()
    renderHook(() => useAutoRefresh(fn, 1000))
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('calls fn again after intervalMs', () => {
    const fn = vi.fn()
    renderHook(() => useAutoRefresh(fn, 1000))
    expect(fn).toHaveBeenCalledTimes(1)
    vi.advanceTimersByTime(1000)
    expect(fn).toHaveBeenCalledTimes(2)
    vi.advanceTimersByTime(1000)
    expect(fn).toHaveBeenCalledTimes(3)
  })

  it('clears interval on unmount — no extra calls after unmount', () => {
    const fn = vi.fn()
    const { unmount } = renderHook(() => useAutoRefresh(fn, 1000))
    expect(fn).toHaveBeenCalledTimes(1)
    unmount()
    vi.advanceTimersByTime(3000)
    expect(fn).toHaveBeenCalledTimes(1)
  })
})
