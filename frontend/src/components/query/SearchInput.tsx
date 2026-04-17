// Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S002
// Task: T002 — SearchInput — 512-char limit + IME guard
// Decision: R005-frontend — isComposing guard for CJK input; AC7/AC8/AC9 enforced
import { useTranslation } from 'react-i18next'

interface SearchInputProps {
  readonly value: string
  readonly onChange: (value: string) => void
  readonly onSubmit: () => void
  readonly isLoading: boolean
  readonly disabled?: boolean
}

export function SearchInput({ value, onChange, onSubmit, isLoading, disabled }: SearchInputProps) {
  const { t } = useTranslation()

  const isOverLimit = value.length > 512
  const isEmpty = value.trim() === ''
  const isDisabled = disabled || isLoading || isOverLimit || isEmpty

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // IME guard: block Enter during CJK composition.
    // nativeEvent.isComposing is the cross-browser standard (Chrome, Firefox, Safari).
    // e.nativeEvent is the underlying DOM KeyboardEvent — isComposing reflects compositionstart/end state.
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      if (!isDisabled) {
        onSubmit()
      }
    }
  }

  return (
    <div className="search-panel">
      <div className="search-input-wrap">
        <textarea
          className="search-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('search.placeholder')}
          disabled={isLoading || !!disabled}
          aria-label={t('search.placeholder')}
        />
      </div>
      <div className="search-footer">
        <span className="token-badge">{t('search.char_count', { count: value.length, max: 512 })}</span>
        <button
          type="button"
          className="btn-search"
          onClick={onSubmit}
          disabled={isDisabled}
        >
          {t('search.button')}
        </button>
      </div>
    </div>
  )
}
