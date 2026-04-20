// Task: T004 (S004) — MetricCards tests
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MetricCards } from '../../src/components/MetricCards'
import type { MetricsData } from '../../src/api/metricsApi'
import '../../src/i18n'

const mockData: MetricsData = {
  documents: { total: 42, ready: 30, processing: 5, error: 7 },
  users: { total: 15, active: 10 },
  groups: { total: 4 },
  queries: { last_7_days: [] },
  health: { database: 'ok', api: 'ok' },
}

describe('MetricCards', () => {
  it('renders total documents card', () => {
    render(<MetricCards data={mockData} />)
    expect(screen.getByText('42')).toBeTruthy()
  })

  it('renders active documents card (ready count)', () => {
    render(<MetricCards data={mockData} />)
    expect(screen.getByText('30')).toBeTruthy()
  })

  it('renders total users card', () => {
    render(<MetricCards data={mockData} />)
    expect(screen.getByText('15')).toBeTruthy()
  })

  it('renders total groups card', () => {
    render(<MetricCards data={mockData} />)
    expect(screen.getByText('4')).toBeTruthy()
  })
})
