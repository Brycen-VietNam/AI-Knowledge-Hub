import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConfidenceBadge } from '../../../src/components/results/ConfidenceBadge'

describe('ConfidenceBadge — HIGH (>= 0.7)', () => {
  it('shows HIGH at exactly 0.7', () => {
    render(<ConfidenceBadge score={0.7} />)
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('shows HIGH at 0.95', () => {
    render(<ConfidenceBadge score={0.95} />)
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('HIGH badge has high variant class', () => {
    render(<ConfidenceBadge score={0.8} />)
    const badge = screen.getByText('HIGH')
    expect(badge.className).toContain('confidence-badge')
    expect(badge.className).toContain('high')
  })
})

describe('ConfidenceBadge — MEDIUM (>= 0.4 and < 0.7)', () => {
  it('shows MEDIUM at exactly 0.4', () => {
    render(<ConfidenceBadge score={0.4} />)
    expect(screen.getByText('MEDIUM')).toBeInTheDocument()
  })

  it('shows MEDIUM at 0.699', () => {
    render(<ConfidenceBadge score={0.699} />)
    expect(screen.getByText('MEDIUM')).toBeInTheDocument()
  })

  it('MEDIUM badge has medium variant class', () => {
    render(<ConfidenceBadge score={0.55} />)
    const badge = screen.getByText('MEDIUM')
    expect(badge.className).toContain('confidence-badge')
    expect(badge.className).toContain('medium')
  })
})

describe('ConfidenceBadge — LOW (< 0.4)', () => {
  it('shows LOW at 0.399', () => {
    render(<ConfidenceBadge score={0.399} />)
    expect(screen.getByText('LOW')).toBeInTheDocument()
  })

  it('shows LOW at 0.0', () => {
    render(<ConfidenceBadge score={0.0} />)
    expect(screen.getByText('LOW')).toBeInTheDocument()
  })

  it('LOW badge has low variant class', () => {
    render(<ConfidenceBadge score={0.2} />)
    const badge = screen.getByText('LOW')
    expect(badge.className).toContain('confidence-badge')
    expect(badge.className).toContain('low')
  })
})
