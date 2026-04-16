// Task: T005 (S003) — LowConfidenceWarning banner
import { useTranslation } from 'react-i18next'

export function LowConfidenceWarning() {
  const { t } = useTranslation()
  return (
    <div role="alert" className="rounded-md bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
      {t('results.low_confidence_warning')}
    </div>
  )
}
