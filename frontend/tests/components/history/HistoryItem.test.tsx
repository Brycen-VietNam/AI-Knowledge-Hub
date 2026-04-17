import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { HistoryItem } from '../../../src/components/history/HistoryItem'
import { QueryHistoryItem } from '../../../src/store/queryStore'

function makeItem(overrides: Partial<QueryHistoryItem> = {}): QueryHistoryItem {
  return {
    id: 'test-id',
    query: 'test query',
    answer: 'test answer',
    citations: [],
    timestamp: new Date('2026-04-16T09:05:00'),
    ...overrides,
  }
}

describe('HistoryItem — truncation', () => {
  it('renders truncated query at 60 chars (plain ASCII)', () => {
    const q = 'a'.repeat(70)
    render(<HistoryItem item={makeItem({ query: q })} onSelect={vi.fn()} />)
    expect(screen.getByTestId('history-query').textContent).toBe('a'.repeat(60) + '\u2026')
  })

  it('truncates CJK string correctly at 60 codepoints', () => {
    const q = '\u3042'.repeat(70) // 70 hiragana chars
    render(<HistoryItem item={makeItem({ query: q })} onSelect={vi.fn()} />)
    expect(screen.getByTestId('history-query').textContent).toBe('\u3042'.repeat(60) + '\u2026')
  })

  it('renders exact query when <= 60 chars', () => {
    const q = 'short query'
    render(<HistoryItem item={makeItem({ query: q })} onSelect={vi.fn()} />)
    expect(screen.getByTestId('history-query').textContent).toBe('short query')
  })
})

describe('HistoryItem — timestamp', () => {
  it('displays HH:mm timestamp', () => {
    const item = makeItem({ timestamp: new Date('2026-04-16T09:05:00') })
    render(<HistoryItem item={item} onSelect={vi.fn()} />)
    expect(screen.getByTestId('history-time').textContent).toBe('09:05')
  })
})

describe('HistoryItem — interaction', () => {
  it('calls onSelect with item when clicked', () => {
    const onSelect = vi.fn()
    const item = makeItem()
    render(<HistoryItem item={item} onSelect={onSelect} />)
    fireEvent.click(screen.getByRole('listitem'))
    expect(onSelect).toHaveBeenCalledWith(item)
  })
})
