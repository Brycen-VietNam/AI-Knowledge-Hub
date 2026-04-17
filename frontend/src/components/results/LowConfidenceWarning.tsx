// Task: T005 (S003) — LowConfidenceWarning banner
// Task: S004/T003 — Replace Tailwind classes with warning-banner CSS
import { useTranslation } from 'react-i18next'

export function LowConfidenceWarning() {
  const { t } = useTranslation()
  return (
    <div role="alert" className="warning-banner">
      <span className="warning-icon">⚠</span>
      {t('results.low_confidence_warning')}
    </div>
  )
}
