// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T007 — LanguageSelector — 4 locales, localStorage persist via i18next-browser-languagedetector
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'

const LANGS = [
  { code: 'en', label: 'lang.en' },
  { code: 'ja', label: 'lang.ja' },
  { code: 'vi', label: 'lang.vi' },
  { code: 'ko', label: 'lang.ko' },
]

export function LanguageSelector() {
  const { t } = useTranslation()

  return (
    <div className="inline-lang">
      <span className="lang-dot" />
      <label htmlFor="admin-lang-selector">{t('lang.selector_label')}</label>
      <select
        id="admin-lang-selector"
        aria-label={t('lang.selector_label')}
        value={i18n.language}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
      >
        {LANGS.map(({ code, label }) => (
          <option key={code} value={code}>{t(label)}</option>
        ))}
      </select>
    </div>
  )
}
