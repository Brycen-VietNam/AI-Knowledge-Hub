import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LowConfidenceWarning } from '../../../src/components/results/LowConfidenceWarning'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key === 'results.low_confidence_warning') {
        return 'This answer has low confidence. Please verify with source documents.'
      }
      return key
    },
  }),
}))

describe('LowConfidenceWarning', () => {
  it('renders the low confidence warning text', () => {
    render(<LowConfidenceWarning />)
    expect(
      screen.getByText('This answer has low confidence. Please verify with source documents.')
    ).toBeInTheDocument()
  })

  it('renders using i18n key (no hardcoded strings)', () => {
    render(<LowConfidenceWarning />)
    // If translation works, we should NOT see the raw key
    expect(screen.queryByText('results.low_confidence_warning')).toBeNull()
  })

  it('has warning role or amber styling', () => {
    render(<LowConfidenceWarning />)
    const el = screen.getByRole('alert')
    expect(el).toBeInTheDocument()
  })
})
