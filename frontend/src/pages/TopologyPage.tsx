import React from 'react'
import { TopologyCanvas3D } from '@/components/topology/TopologyCanvas3D'
import { useDevices } from '@/hooks/useDevices'
import { useAlerts } from '@/hooks/useAlerts'

export const TopologyPage: React.FC = () => {
  const { data: devicesData } = useDevices()
  const { data: alertsData } = useAlerts({ resolved: false })

  return (
    <div className="relative w-full h-full overflow-hidden">
      {/* Top Floating Info Bar */}
      <div className="absolute top-6 left-6 z-20 flex items-center gap-3 p-3 rounded-xl bg-surface-950/85 backdrop-blur-md border border-white/10 shadow-2xl">
        <div>
          <h2 className="text-sm font-bold font-mono text-white flex items-center gap-2">
            3D Network Topology
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Interactive WebGL
            </span>
          </h2>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            {devicesData?.total || 0} Nodes • {alertsData?.total || 0} Active Alerts
          </p>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute top-6 right-6 z-20 hidden md:flex items-center gap-4 p-3 rounded-xl bg-surface-950/85 backdrop-blur-md border border-white/10 text-xs font-mono">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
          <span className="text-slate-300">Healthy / UP</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-[0_0_8px_#fbbf24]" />
          <span className="text-slate-300">Warning</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_8px_#f43f5e]" />
          <span className="text-slate-300">Critical</span>
        </div>
      </div>

      {/* 3D Canvas */}
      <TopologyCanvas3D className="w-full h-full" />
    </div>
  )
}
