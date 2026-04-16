// Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S002
// Task: T003 — LanguageSelector — 4 locales + localStorage persist
// Decision: D003 — UI language in localStorage key "lang"; token NEVER in localStorage
import { useTranslation } from 'react-i18next'
import i18n from '../../i18n'

const LANGUAGE_OPTIONS = [
  { value: 'ja', label: '日本語' },
  { value: 'en', label: 'English' },
  { value: 'vi', label: 'Tiếng Việt' },
  { value: 'ko', label: '한국어' },
]

export function LanguageSelector() {
  const { t } = useTranslation()

  function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const lang = e.target.value
    i18n.changeLanguage(lang)
    localStorage.setItem('lang', lang)
  }

  return (
    <div>
      <label htmlFor="lang-selector">{t('lang.selector_label')}</label>
      <select
        id="lang-selector"
        value={i18n.language}
        onChange={handleChange}
        aria-label={t('lang.selector_label')}
      >
        {LANGUAGE_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
}
