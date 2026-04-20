// Task: T006 (S004) — HealthIndicators tests
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { HealthIndicators } from '../../src/components/HealthIndicators'
import '../../src/i18n'

describe('HealthIndicators', () => {
  it('renders "Online" for both when all ok', () => {
    render(<HealthIndicators health={{ database: 'ok', api: 'ok' }} />)
    const onlines = screen.getAllByText(/Online/)
    expect(onlines).toHaveLength(2)
  })

  it('renders "Offline" for database when database=error', () => {
    render(<HealthIndicators health={{ database: 'error', api: 'ok' }} />)
    expect(screen.getByText(/Database: Offline/)).toBeTruthy()
    expect(screen.getByText(/Backend API: Online/)).toBeTruthy()
  })

  it('renders "Offline" for api when api=error', () => {
    render(<HealthIndicators health={{ database: 'ok', api: 'error' }} />)
    expect(screen.getByText(/Database: Online/)).toBeTruthy()
    expect(screen.getByText(/Backend API: Offline/)).toBeTruthy()
  })

  it('renders "Offline" for both when both error', () => {
    render(<HealthIndicators health={{ database: 'error', api: 'error' }} />)
    const offlines = screen.getAllByText(/Offline/)
    expect(offlines).toHaveLength(2)
  })
})
