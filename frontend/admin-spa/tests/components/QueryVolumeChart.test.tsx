// Task: T005 (S004) — QueryVolumeChart tests
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { DailyQueryCount } from '../../src/api/metricsApi'
import '../../src/i18n'

// Mock recharts — avoid SVG rendering issues in jsdom
vi.mock('recharts', () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// Import AFTER mock is registered
const { QueryVolumeChart } = await import('../../src/components/QueryVolumeChart')

const sampleData: DailyQueryCount[] = [
  { date: '2026-04-14', count: 12 },
  { date: '2026-04-15', count: 8 },
]

describe('QueryVolumeChart', () => {
  it('renders chart wrapper with data', () => {
    render(<QueryVolumeChart data={sampleData} />)
    expect(screen.getByTestId('bar-chart')).toBeTruthy()
  })

  it('renders without crash when data is empty array', () => {
    const { container } = render(<QueryVolumeChart data={[]} />)
    expect(container.firstChild).toBeTruthy()
  })

  it('renders chart title', () => {
    render(<QueryVolumeChart data={sampleData} />)
    expect(screen.getByText('Query Volume (Last 7 Days)')).toBeTruthy()
  })
})
