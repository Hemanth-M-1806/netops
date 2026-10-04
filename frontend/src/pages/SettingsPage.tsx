import React from 'react'
import { Settings, Shield, Server, Database, Activity, CheckCircle2 } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { useQuery } from '@tanstack/react-query'
import { healthApi } from '@/services/api'

export const SettingsPage: React.FC = () => {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.check,
  })

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold font-mono tracking-tight text-white flex items-center gap-3">
          NOC System Configuration
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Backend API connections, telemetry pipeline settings, and database status.
        </p>
      </div>

      {/* Service Health Card */}
      <Card className="space-y-4">
        <h3 className="font-mono font-bold text-sm text-white flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          Microservice Topology Status
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400">
              <span>FastAPI Backend</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
            </div>
            <div className="font-mono text-base font-bold text-white">Port 8000</div>
            <div className="text-[11px] font-mono text-emerald-400">
              {health?.status === 'healthy' ? 'Status: ONLINE' : 'Status: CONNECTING'}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400">
              <span>MySQL Database</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
            </div>
            <div className="font-mono text-base font-bold text-white">Port 3306</div>
            <div className="text-[11px] font-mono text-emerald-400">
              {health?.database === 'connected' ? 'aiomysql: CONNECTED' : 'UNREACHABLE'}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400">
              <span>Collector Layer</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
            </div>
            <div className="font-mono text-base font-bold text-white">Port 8100</div>
            <div className="text-[11px] font-mono text-emerald-400">Normalizing & Forwarding</div>
          </div>
        </div>
      </Card>

      {/* Telemetry Architecture Specs */}
      <Card className="space-y-4">
        <h3 className="font-mono font-bold text-sm text-white flex items-center gap-2">
          <Database className="w-4 h-4 text-purple-400" />
          Telemetry Pipeline Specifications
        </h3>

        <div className="space-y-3 text-xs font-mono text-slate-300">
          <div className="flex items-center justify-between py-2 border-b border-white/[0.06]">
            <span className="text-slate-400">Ingest Path:</span>
            <span className="text-cyan-400">Simulator (or Network) → Collector :8100 → Backend :8000/api/v1/telemetry/ingest</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-white/[0.06]">
            <span className="text-slate-400">Database Engine:</span>
            <span className="text-slate-200">MySQL 8.0 (Pure SQL, Zero-ORM aiomysql pool)</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-white/[0.06]">
            <span className="text-slate-400">Anomaly Scoring Formula:</span>
            <span className="text-slate-200">Rolling Z-score + Drop/Error Impact Weights (dynamic threshold &gt; 3.0σ)</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-white/[0.06]">
            <span className="text-slate-400">RAG Context Engine:</span>
            <span className="text-slate-200">In-memory real-time prompt augmentation with live MySQL state</span>
          </div>
        </div>
      </Card>
    </div>
  )
}
