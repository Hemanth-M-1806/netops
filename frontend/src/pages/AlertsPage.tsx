import React, { useState } from 'react'
import { ShieldAlert, CheckCircle2, Filter, AlertTriangle } from 'lucide-react'
import { useAlerts } from '@/hooks/useAlerts'
import { AlertTable } from '@/components/alerts/AlertTable'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { Severity } from '@/types'

export const AlertsPage: React.FC = () => {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL')
  const [resolvedFilter, setResolvedFilter] = useState<boolean | undefined>(false)

  const { data: alertsData, isLoading } = useAlerts({
    severity: severityFilter === 'ALL' ? undefined : severityFilter,
    resolved: resolvedFilter,
    limit: 100,
  })

  const alerts = alertsData?.items || []

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-mono tracking-tight text-white flex items-center gap-3">
            Alert Triage Center
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/30">
              {alertsData?.total || 0} ALERTS
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Dynamic anomaly detection triggered by live Z-score calculation on telemetry metrics.
          </p>
        </div>
      </div>

      {/* Filter Row */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-surface-900/60 border border-white/[0.06]">
        {/* Severity Tabs */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400 mr-2 flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5" /> Severity:
          </span>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors cursor-pointer ${
                severityFilter === sev
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-surface-950 text-slate-400 border border-white/[0.06] hover:text-white'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        {/* Resolved Status Toggle */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400 mr-2">Status:</span>
          <button
            onClick={() => setResolvedFilter(false)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors cursor-pointer ${
              resolvedFilter === false
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                : 'bg-surface-950 text-slate-400 border border-white/[0.06] hover:text-white'
            }`}
          >
            Active Only
          </button>
          <button
            onClick={() => setResolvedFilter(true)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors cursor-pointer ${
              resolvedFilter === true
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'bg-surface-950 text-slate-400 border border-white/[0.06] hover:text-white'
            }`}
          >
            Resolved
          </button>
          <button
            onClick={() => setResolvedFilter(undefined)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors cursor-pointer ${
              resolvedFilter === undefined
                ? 'bg-slate-700 text-slate-200 border border-white/20'
                : 'bg-surface-950 text-slate-400 border border-white/[0.06] hover:text-white'
            }`}
          >
            All
          </button>
        </div>
      </div>

      {/* Alerts Table */}
      <Card className="p-0 overflow-hidden">
        <AlertTable alerts={alerts} isLoading={isLoading} />
      </Card>
    </div>
  )
}
