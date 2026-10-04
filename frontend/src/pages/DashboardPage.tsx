import React from 'react'
import { Server, ShieldAlert, Cpu, Activity, ArrowRight, Network, Sparkles } from 'lucide-react'
import { MetricCard } from '@/components/metrics/MetricCard'
import { AlertTable } from '@/components/alerts/AlertTable'
import { TrafficChart } from '@/components/metrics/TrafficChart'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { useDevices } from '@/hooks/useDevices'
import { useAlerts } from '@/hooks/useAlerts'
import { useInterfaceMetrics } from '@/hooks/useTelemetry'
import { useNavigate } from 'react-router-dom'
import { TopologyCanvas3D } from '@/components/topology/TopologyCanvas3D'

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const { data: devicesData } = useDevices()
  const { data: alertsData, isLoading: alertsLoading } = useAlerts({ resolved: false, limit: 10 })
  // Sample telemetry from interface 10 (R1/Gi0/0) or 20 (R2/Gi0/0)
  const { data: metricsData } = useInterfaceMetrics(10, { limit: 25 })

  const totalDevices = devicesData?.total || 0
  const activeAlerts = alertsData?.total || 0
  const criticalCount =
    alertsData?.items.filter((a) => a.severity === 'CRITICAL' || a.severity === 'HIGH').length || 0

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-mono tracking-tight text-white flex items-center gap-3">
            Operations Command Center
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              ALL SYSTEMS ONLINE
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time automated telemetry ingest, ML risk analysis, and AI-assisted troubleshooting.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/topology')}
            className="font-mono text-xs gap-2"
          >
            <Network className="w-4 h-4 text-cyan-400" />
            <span>Open 3D Topology</span>
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/copilot')}
            className="font-mono text-xs gap-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>AI Copilot</span>
          </Button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Monitored Devices"
          value={totalDevices}
          subtitle="6 Core & Perimeter"
          trend="+0 offline"
          trendPositive={true}
          icon={Server}
          iconColor="text-blue-400"
        />
        <MetricCard
          title="Active Alerts"
          value={activeAlerts}
          subtitle={`${criticalCount} High / Critical`}
          trend={criticalCount > 0 ? 'Requires Review' : 'Nominal'}
          trendPositive={criticalCount === 0}
          icon={ShieldAlert}
          iconColor={criticalCount > 0 ? 'text-rose-400' : 'text-emerald-400'}
        />
        <MetricCard
          title="Network Status"
          value="Healthy"
          subtitle="Z-Score Anomaly Detector: ON"
          trend="99.98% SLA"
          trendPositive={true}
          icon={Activity}
          iconColor="text-emerald-400"
        />
        <MetricCard
          title="Telemetry Ingest"
          value="Continuous"
          subtitle="FastAPI + MySQL Ingest Layer"
          trend="Live Stream"
          trendPositive={true}
          icon={Cpu}
          iconColor="text-purple-400"
        />
      </div>

      {/* Grid: 3D Topology Mini-Viewer + Traffic Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 3D Topology card */}
        <Card className="lg:col-span-7 h-[420px] p-0 overflow-hidden relative flex flex-col">
          <div className="p-4 border-b border-white/[0.08] bg-surface-900/60 flex items-center justify-between z-10">
            <div className="flex items-center gap-2">
              <Network className="w-4 h-4 text-cyan-400" />
              <span className="font-mono text-xs font-semibold uppercase text-slate-200">
                Live 3D Topology
              </span>
            </div>
            <button
              onClick={() => navigate('/topology')}
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span>Full Screen View</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="flex-1 relative">
            <TopologyCanvas3D className="h-full w-full" />
          </div>
        </Card>

        {/* Live Traffic Chart */}
        <Card className="lg:col-span-5 h-[420px] flex flex-col justify-between">
          <TrafficChart
            metrics={metricsData?.items || []}
            title="Core Router Telemetry (R1 Gi0/0)"
          />
          <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Dynamic Anomaly Threshold: Active</span>
            <span className="text-cyan-400">Live Ingest</span>
          </div>
        </Card>
      </div>

      {/* Recent Alerts Feed Table */}
      <Card className="p-0 overflow-hidden">
        <div className="p-4 border-b border-white/[0.08] bg-surface-900/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <span className="font-mono text-xs font-semibold uppercase text-slate-200">
              Active Network Alerts ({alertsData?.total || 0})
            </span>
          </div>
          <button
            onClick={() => navigate('/alerts')}
            className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
          >
            <span>Triage All Alerts</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
        <AlertTable alerts={alertsData?.items || []} isLoading={alertsLoading} />
      </Card>
    </div>
  )
}
