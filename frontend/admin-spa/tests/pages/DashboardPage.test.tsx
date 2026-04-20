// Task: T007 (S004) — DashboardPage tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { DashboardPage } from '../../src/pages/DashboardPage'
import * as metricsApi from '../../src/api/metricsApi'
import type { MetricsData } from '../../src/api/metricsApi'
import { useAuthStore } from '../../src/store/authStore'
import '../../src/i18n'

// Stub useAdminGuard — no redirect side-effects in tests
vi.mock('../../src/hooks/useAdminGuard', () => ({ useAdminGuard: vi.fn() }))

// Mock recharts to avoid jsdom SVG issues
vi.mock('recharts', () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

const sampleMetrics: MetricsData = {
  documents: { total: 42, ready: 30, processing: 5, error: 7 },
  users: { total: 15, active: 10 },
  groups: { total: 4 },
  queries: { last_7_days: [{ date: '2026-04-14', count: 8 }] },
  health: { database: 'ok', api: 'ok' },
}

beforeEach(() => {
  vi.restoreAllMocks()
  useAuthStore.setState({
    token: 'test-token',
    username: 'admin',
    isAdmin: true,
    sessionExpiredMessage: null,
    _refreshTimer: null,
  })
})

describe('DashboardPage', () => {
  it('renders metric cards when fetch succeeds', async () => {
    vi.spyOn(metricsApi, 'getMetrics').mockResolvedValue(sampleMetrics)
    await act(async () => {
      render(<DashboardPage />)
    })
    expect(screen.getByText('42')).toBeTruthy()  // total docs
    expect(screen.getByText('30')).toBeTruthy()  // active docs (ready)
    expect(screen.getByText('15')).toBeTruthy()  // total users
    expect(screen.getByText('4')).toBeTruthy()   // total groups
  })

  it('shows "Metrics unavailable" when fetch fails (AC7)', async () => {
    vi.spyOn(metricsApi, 'getMetrics').mockRejectedValue(new Error('network'))
    await act(async () => {
      render(<DashboardPage />)
    })
    expect(screen.getByText('Metrics unavailable')).toBeTruthy()
  })

  it('does not crash when data is null (initial state)', () => {
    vi.spyOn(metricsApi, 'getMetrics').mockReturnValue(new Promise(() => {})) // never resolves
    const { container } = render(<DashboardPage />)
    expect(container.firstChild).toBeTruthy()
  })

  it('calls getMetrics on mount', async () => {
    const spy = vi.spyOn(metricsApi, 'getMetrics').mockResolvedValue(sampleMetrics)
    await act(async () => {
      render(<DashboardPage />)
    })
    expect(spy).toHaveBeenCalledTimes(1)
  })

  it('renders HealthIndicators with health data', async () => {
    vi.spyOn(metricsApi, 'getMetrics').mockResolvedValue(sampleMetrics)
    await act(async () => {
      render(<DashboardPage />)
    })
    const onlines = screen.getAllByText(/Online/)
    expect(onlines.length).toBeGreaterThanOrEqual(2)
  })

  it('renders QueryVolumeChart wrapper', async () => {
    vi.spyOn(metricsApi, 'getMetrics').mockResolvedValue(sampleMetrics)
    await act(async () => {
      render(<DashboardPage />)
    })
    expect(screen.getByTestId('bar-chart')).toBeTruthy()
  })
})
