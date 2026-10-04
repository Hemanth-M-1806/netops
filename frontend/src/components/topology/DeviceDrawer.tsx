import React from 'react'
import { X, Bot, AlertTriangle, Activity, ArrowRight, ShieldCheck, Cpu } from 'lucide-react'
import { useTopologyStore } from '@/stores/useTopologyStore'
import { useDevice, useDeviceInterfaces } from '@/hooks/useDevices'
import { useAlerts } from '@/hooks/useAlerts'
import { useCopilotStore } from '@/stores/useCopilotStore'
import { useNavigate } from 'react-router-dom'
import { getDeviceStatusColor } from '@/utils/formatters'
import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

export const DeviceDrawer: React.FC = () => {
  const { selectedDeviceId, isDrawerOpen, closeDrawer, setSelectedInterfaceId } =
    useTopologyStore()
  const navigate = useNavigate()
  const { setTargetDeviceId } = useCopilotStore()

  const { data: device, isLoading: deviceLoading } = useDevice(selectedDeviceId)
  const { data: interfacesData, isLoading: interfacesLoading } =
    useDeviceInterfaces(selectedDeviceId)
  const { data: alertsData } = useAlerts({
    device_id: selectedDeviceId || undefined,
    resolved: false,
  })

  if (!isDrawerOpen || !selectedDeviceId) return null

  const handleAskCopilot = () => {
    setTargetDeviceId(selectedDeviceId)
    navigate('/copilot')
  }

  const statusColor = device ? getDeviceStatusColor(device.status) : null

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-surface-950/95 backdrop-blur-xl border-l border-white/10 z-40 shadow-2xl flex flex-col transition-all duration-300 animate-in slide-in-from-right">
      {/* Header */}
      <div className="p-5 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-surface-900 border border-white/10 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white font-mono">
              {device?.hostname || 'Device Inspector'}
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              {device?.ip_address || 'Loading...'}
            </p>
          </div>
        </div>
        <button
          onClick={closeDrawer}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {deviceLoading ? (
        <LoadingSpinner label="Fetching device telemetry..." />
      ) : device ? (
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Status & Type */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-surface-900/60 border border-white/[0.06]">
              <div className="text-[10px] font-mono uppercase text-slate-400">Status</div>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: statusColor?.hex }}
                />
                <span className="font-mono text-sm font-semibold text-slate-200">
                  {device.status}
                </span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-surface-900/60 border border-white/[0.06]">
              <div className="text-[10px] font-mono uppercase text-slate-400">Type</div>
              <div className="font-mono text-sm font-semibold text-cyan-400 mt-1 uppercase">
                {device.device_type}
              </div>
            </div>
          </div>

          {/* Active Alerts */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-semibold uppercase text-slate-400">
                Active Alerts
              </span>
              <span className="text-xs font-mono text-rose-400 font-bold">
                {alertsData?.total || 0}
              </span>
            </div>
            {alertsData && alertsData.items.length > 0 ? (
              <div className="space-y-2">
                {alertsData.items.slice(0, 3).map((alert) => (
                  <div
                    key={alert.id}
                    className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs"
                  >
                    <div className="flex items-center justify-between font-mono font-medium text-rose-400 mb-1">
                      <span>{alert.alert_type}</span>
                      <span className="text-[10px] px-1 rounded bg-rose-500/20">
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-slate-300 text-[11px] leading-relaxed line-clamp-2">
                      {alert.message}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/15 text-xs text-emerald-400 flex items-center gap-2 font-mono">
                <ShieldCheck className="w-4 h-4" />
                <span>No active alerts on this device</span>
              </div>
            )}
          </div>

          {/* Interfaces */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-semibold uppercase text-slate-400">
                Interfaces ({interfacesData?.items.length || 0})
              </span>
            </div>
            {interfacesLoading ? (
              <div className="text-xs text-slate-400 font-mono py-2">Loading interfaces...</div>
            ) : interfacesData && interfacesData.items.length > 0 ? (
              <div className="space-y-1.5">
                {interfacesData.items.map((iface) => (
                  <div
                    key={iface.id}
                    className="p-2.5 rounded-lg bg-surface-900/60 border border-white/[0.06] flex items-center justify-between text-xs hover:border-cyan-500/30 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          iface.status === 'UP' ? 'bg-emerald-400' : 'bg-red-500'
                        }`}
                      />
                      <span className="font-mono text-slate-200 font-medium">
                        {iface.name}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">
                      {iface.speed_bps ? `${iface.speed_bps / 1000000}M` : 'Virtual'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-500 font-mono">No interfaces discovered</div>
            )}
          </div>
        </div>
      ) : null}

      {/* Footer Action */}
      <div className="p-4 border-t border-white/10 bg-surface-950/80 space-y-2">
        <Button
          onClick={handleAskCopilot}
          variant="primary"
          className="w-full justify-center gap-2 text-xs font-mono"
        >
          <Bot className="w-4 h-4" />
          <span>Ask Copilot About {device?.hostname || 'Device'}</span>
        </Button>
      </div>
    </div>
  )
}
