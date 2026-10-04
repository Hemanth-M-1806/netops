import React from 'react'
import { Sparkles, Bot, ShieldCheck, Database, Zap } from 'lucide-react'
import { CopilotChat } from '@/components/copilot/CopilotChat'
import { Card } from '@/components/common/Card'
import { useDevices } from '@/hooks/useDevices'
import { useCopilotStore } from '@/stores/useCopilotStore'

export const CopilotPage: React.FC = () => {
  const { data: devicesData } = useDevices()
  const { targetDeviceId, setTargetDeviceId } = useCopilotStore()

  const devices = devicesData?.items || []

  return (
    <div className="p-8 h-full max-w-7xl mx-auto flex flex-col space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-mono tracking-tight text-white flex items-center gap-3">
            NetOps AI Copilot
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/30">
              RAG PIPELINE ACTIVE
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            LLM assistant grounded in your live MySQL network topology, interfaces, and ML anomaly telemetry.
          </p>
        </div>

        {/* Scope selector */}
        <div className="flex items-center gap-3">
          <label className="text-xs font-mono text-slate-400">Context Scope:</label>
          <select
            value={targetDeviceId || ''}
            onChange={(e) =>
              setTargetDeviceId(e.target.value ? Number(e.target.value) : null)
            }
            className="bg-surface-900 border border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-400"
          >
            <option value="">Global Network (All Devices)</option>
            {devices.map((d) => (
              <option key={d.device_id} value={d.device_id}>
                {d.hostname} ({d.ip_address})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Chat Component */}
        <div className="lg:col-span-8 h-[650px] flex flex-col">
          <CopilotChat />
        </div>

        {/* Side Info & Architecture info */}
        <div className="lg:col-span-4 space-y-4">
          <Card className="space-y-4">
            <h3 className="font-mono font-bold text-sm text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-cyan-400" />
              RAG Architecture
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Unlike generic LLM bots, NetOps Copilot is injected with the real-time operational context of your network on every single prompt.
            </p>

            <div className="space-y-3 pt-2">
              <div className="flex items-start gap-3 text-xs">
                <div className="p-2 rounded-lg bg-surface-900 border border-white/10 text-cyan-400 shrink-0">
                  <Database className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-mono font-bold text-slate-200">Raw MySQL Grounding</div>
                  <div className="text-slate-400 text-[11px]">
                    Direct telemetry samples, drop ratios, and recent error bursts are pulled without ORM overhead.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 text-xs">
                <div className="p-2 rounded-lg bg-surface-900 border border-white/10 text-purple-400 shrink-0">
                  <ShieldCheck className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-mono font-bold text-slate-200">Dynamic Risk Anomaly Scores</div>
                  <div className="text-slate-400 text-[11px]">
                    Z-scores and impact weights are supplied directly to assist in root-cause diagnosis.
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
