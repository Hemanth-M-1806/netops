import React, { useState, useEffect } from 'react'
import { Activity, Bell, RefreshCw, Sparkles, Terminal } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { healthApi } from '@/services/api'
import { useAlerts } from '@/hooks/useAlerts'
import { useNavigate } from 'react-router-dom'

export const Header: React.FC = () => {
  const navigate = useNavigate()
  const [time, setTime] = useState(new Date().toUTCString().slice(17, 25) + ' UTC')

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toUTCString().slice(17, 25) + ' UTC')
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.check,
    refetchInterval: 10000,
  })

  const { data: alertsData } = useAlerts({ resolved: false, limit: 1 })
  const activeAlertsCount = alertsData?.total || 0

  const isHealthy = health?.status === 'healthy' && health?.database === 'connected'

  return (
    <header className="h-16 border-b border-white/[0.08] bg-surface-950/80 backdrop-blur-md px-6 flex items-center justify-between z-30 sticky top-0">
      {/* Left: Branding & Status */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.4)]">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-white text-base">NetOps</span>
              <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                v{health?.version || '0.1.0'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono -mt-0.5">
              TELEMETRY & AI COPILOT
            </p>
          </div>
        </div>

        {/* Backend health status badge */}
        <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-surface-900 border border-white/[0.06] text-xs font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              healthLoading
                ? 'bg-amber-400 animate-pulse'
                : isHealthy
                ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]'
                : 'bg-rose-500 shadow-[0_0_8px_#f43f5e]'
            }`}
          />
          <span className="text-slate-300">
            {healthLoading ? 'CONNECTING...' : isHealthy ? 'NOC LIVE' : 'BACKEND DOWN'}
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">{time}</span>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Alerts quick badge */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-900 hover:bg-surface-800 border border-white/[0.08] text-xs font-mono text-slate-300 transition-colors cursor-pointer"
        >
          <Bell className="w-4 h-4 text-amber-400" />
          <span>ALERTS</span>
          {activeAlertsCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px] font-bold shadow-[0_0_8px_rgba(244,63,94,0.6)]">
              {activeAlertsCount}
            </span>
          )}
        </button>

        {/* AI Copilot quick toggle */}
        <button
          onClick={() => navigate('/copilot')}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-purple-500/20 to-cyan-500/20 hover:from-purple-500/30 hover:to-cyan-500/30 border border-cyan-500/30 text-xs font-medium text-cyan-300 transition-all shadow-[0_0_12px_rgba(6,182,212,0.15)] cursor-pointer"
        >
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-mono">COPILOT</span>
        </button>
      </div>
    </header>
  )
}
