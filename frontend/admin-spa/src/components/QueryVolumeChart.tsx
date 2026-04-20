// Spec: docs/admin-spa/spec/admin-spa.spec.md#S004
// Task: T005 (S004) — QueryVolumeChart — 7-day BarChart (AC3)
// Tree-shake: import only used recharts components
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { useTranslation } from 'react-i18next'
import type { DailyQueryCount } from '../api/metricsApi'

interface Props {
  data: DailyQueryCount[]
}

export function QueryVolumeChart({ data }: Props) {
  const { t } = useTranslation()
  const chartData = data.map((d) => ({
    name: d.date.slice(5),  // "MM-DD" from "YYYY-MM-DD"
    value: d.count,
  }))

  return (
    <div className="query-volume-chart">
      <h2 className="chart-title">{t('dashboard.chart_title')}</h2>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={chartData}>
          <XAxis dataKey="name" />
          <YAxis label={{ value: t('dashboard.chart_y_label'), angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Bar dataKey="value" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
