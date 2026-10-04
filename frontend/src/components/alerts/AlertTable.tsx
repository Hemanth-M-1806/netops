import React from 'react'
import { Alert, Severity } from '@/types'
import { AlertBadge } from './AlertBadge'
import { formatTimeAgo } from '@/utils/formatters'
import { CheckCircle2, Bot } from 'lucide-react'
import { useResolveAlert } from '@/hooks/useAlerts'
import { useCopilotStore } from '@/stores/useCopilotStore'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/common/Button'

interface AlertTableProps {
  alerts: Alert[]
  isLoading?: boolean
}

export const AlertTable: React.FC<AlertTableProps> = ({ alerts, isLoading }) => {
  const resolveAlertMutation = useResolveAlert()
  const { setTargetDeviceId, addMessage } = useCopilotStore()
  const navigate = useNavigate()

  const handleResolve = (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    resolveAlertMutation.mutate(id)
  }

  const handleInvestigateWithCopilot = (alert: Alert) => {
    if (alert.interface_id) {
      // Find or set device if available
    }
    navigate('/copilot')
  }

  if (isLoading) {
    return (
      <div className="p-8 text-center text-xs font-mono text-slate-400">
        Loading network alerts...
      </div>
    )
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div className="p-12 text-center text-slate-400">
        <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
        <p className="font-mono text-sm text-slate-300">No active alerts matching criteria</p>
        <p className="font-mono text-xs text-slate-500 mt-1">Network operation is nominal</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs font-mono">
        <thead className="border-b border-white/[0.08] text-[11px] text-slate-400 bg-surface-900/40 uppercase">
          <tr>
            <th className="py-3 px-4 font-semibold">Severity</th>
            <th className="py-3 px-4 font-semibold">Device / Interface</th>
            <th className="py-3 px-4 font-semibold">Type</th>
            <th className="py-3 px-4 font-semibold">Diagnosis</th>
            <th className="py-3 px-4 font-semibold">Triggered</th>
            <th className="py-3 px-4 font-semibold text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.04]">
          {alerts.map((alert) => (
            <tr
              key={alert.id}
              className={`hover:bg-white/[0.02] transition-colors ${
                alert.resolved ? 'opacity-50' : ''
              }`}
            >
              <td className="py-3.5 px-4 whitespace-nowrap">
                <AlertBadge severity={alert.severity} />
              </td>
              <td className="py-3.5 px-4 whitespace-nowrap">
                <div className="font-semibold text-slate-200">
                  {alert.hostname || 'Device'}
                </div>
                <div className="text-[11px] text-slate-400">
                  {alert.interface_name || `IF #${alert.interface_id}`}
                </div>
              </td>
              <td className="py-3.5 px-4 whitespace-nowrap text-cyan-400 font-medium">
                {alert.alert_type}
              </td>
              <td className="py-3.5 px-4 max-w-md text-slate-300 font-sans text-xs">
                {alert.message}
              </td>
              <td className="py-3.5 px-4 whitespace-nowrap text-slate-400">
                {formatTimeAgo(alert.triggered_at)}
              </td>
              <td className="py-3.5 px-4 whitespace-nowrap text-right space-x-2">
                {!alert.resolved && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => handleResolve(alert.id, e)}
                    isLoading={resolveAlertMutation.isPending}
                    className="text-[11px] py-1 px-2.5 h-7 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10"
                  >
                    Resolve
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleInvestigateWithCopilot(alert)}
                  className="text-[11px] py-1 px-2.5 h-7 text-cyan-400 hover:bg-cyan-500/10"
                  title="Investigate with AI Copilot"
                >
                  <Bot className="w-3.5 h-3.5" />
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
