import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Network,
  Server,
  ShieldAlert,
  Bot,
  Settings,
} from 'lucide-react'
import { useAlerts } from '@/hooks/useAlerts'

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/topology', label: '3D Topology', icon: Network },
  { to: '/devices', label: 'Inventory', icon: Server },
  { to: '/alerts', label: 'Alerts', icon: ShieldAlert, badgeKey: 'alerts' },
  { to: '/copilot', label: 'AI Copilot', icon: Bot },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export const Sidebar: React.FC = () => {
  const { data: alertsData } = useAlerts({ resolved: false, limit: 1 })
  const activeAlertsCount = alertsData?.total || 0

  return (
    <aside className="w-64 border-r border-white/[0.08] bg-surface-950/60 backdrop-blur-md flex flex-col justify-between p-4 shrink-0">
      <div className="space-y-6">
        <div>
          <div className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500 px-3 mb-2">
            Operations
          </div>
          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 group ${
                      isActive
                        ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4 transition-transform group-hover:scale-110" />
                    <span>{item.label}</span>
                  </div>
                  {item.badgeKey === 'alerts' && activeAlertsCount > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-mono font-bold">
                      {activeAlertsCount}
                    </span>
                  )}
                </NavLink>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Bottom status box */}
      <div className="p-3.5 rounded-xl bg-surface-900/60 border border-white/[0.06] text-xs space-y-2">
        <div className="flex items-center justify-between text-slate-400 font-mono text-[11px]">
          <span>TELEMETRY STREAM</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        </div>
        <div className="text-slate-300 font-mono text-[11px]">
          Ingest Rate: <span className="text-cyan-400 font-bold">Live</span>
        </div>
        <div className="w-full bg-surface-950 rounded-full h-1.5 overflow-hidden">
          <div className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full w-[78%]" />
        </div>
      </div>
    </aside>
  )
}
