import React, { useState } from 'react'
import { Server, Search, Network, Bot, CheckCircle, AlertTriangle } from 'lucide-react'
import { useDevices } from '@/hooks/useDevices'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { Badge } from '@/components/common/Badge'
import { getDeviceStatusColor } from '@/utils/formatters'
import { useNavigate } from 'react-router-dom'
import { useTopologyStore } from '@/stores/useTopologyStore'
import { useCopilotStore } from '@/stores/useCopilotStore'

export const DevicesPage: React.FC = () => {
  const navigate = useNavigate()
  const { data: devicesData, isLoading } = useDevices()
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const { selectDevice } = useTopologyStore()
  const { setTargetDeviceId } = useCopilotStore()

  const devices = devicesData?.items || []

  const filteredDevices = devices.filter((d) => {
    const matchesSearch =
      d.hostname.toLowerCase().includes(search.toLowerCase()) ||
      d.ip_address.toLowerCase().includes(search.toLowerCase())
    const matchesType = typeFilter === 'ALL' || d.device_type === typeFilter
    return matchesSearch && matchesType
  })

  const handleInspect3D = (deviceId: number) => {
    selectDevice(deviceId)
    navigate('/topology')
  }

  const handleAskCopilot = (deviceId: number) => {
    setTargetDeviceId(deviceId)
    navigate('/copilot')
  }

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-mono tracking-tight text-white flex items-center gap-3">
            Device Inventory
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">
              {devices.length} NODES
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Core routers, distribution switches, firewalls, and edge access points.
          </p>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search hostname or IP..."
            className="w-full pl-10 pr-4 py-2 bg-surface-900 border border-white/10 rounded-xl text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-400"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
          {['ALL', 'router', 'switch', 'firewall', 'access_point'].map((type) => (
            <button
              key={type}
              onClick={() => setTypeFilter(type)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors cursor-pointer uppercase ${
                typeFilter === type
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-surface-900 text-slate-400 border border-white/[0.06] hover:text-white'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Devices Table Card */}
      <Card className="p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-xs font-mono text-slate-400">
            Loading device inventory...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="border-b border-white/[0.08] text-[11px] text-slate-400 bg-surface-900/40 uppercase">
                <tr>
                  <th className="py-3 px-5 font-semibold">Device</th>
                  <th className="py-3 px-5 font-semibold">IP Address</th>
                  <th className="py-3 px-5 font-semibold">Type</th>
                  <th className="py-3 px-5 font-semibold">Status</th>
                  <th className="py-3 px-5 font-semibold">Description</th>
                  <th className="py-3 px-5 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredDevices.map((d) => {
                  const statusColors = getDeviceStatusColor(d.status)
                  return (
                    <tr key={d.device_id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-4 px-5 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-surface-900 border border-white/10 flex items-center justify-center">
                            <Server className="w-4 h-4 text-cyan-400" />
                          </div>
                          <div>
                            <span className="font-bold text-slate-100 text-sm">{d.hostname}</span>
                            <div className="text-[10px] text-slate-500 font-mono">ID #{d.device_id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-5 whitespace-nowrap font-mono text-slate-300">
                        {d.ip_address}
                      </td>
                      <td className="py-4 px-5 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded bg-surface-900 text-cyan-400 border border-white/10 text-[10px] uppercase font-bold">
                          {d.device_type}
                        </span>
                      </td>
                      <td className="py-4 px-5 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md font-mono text-[10px] font-bold border ${statusColors.badge}`}
                        >
                          <span
                            className="w-1.5 h-1.5 rounded-full"
                            style={{ backgroundColor: statusColors.hex }}
                          />
                          {d.status}
                        </span>
                      </td>
                      <td className="py-4 px-5 text-slate-400 font-sans text-xs">
                        {d.description || '—'}
                      </td>
                      <td className="py-4 px-5 whitespace-nowrap text-right space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleInspect3D(d.device_id)}
                          className="text-[11px] py-1 px-2.5 h-7 gap-1.5"
                        >
                          <Network className="w-3.5 h-3.5 text-cyan-400" />
                          <span>3D View</span>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleAskCopilot(d.device_id)}
                          className="text-[11px] py-1 px-2.5 h-7 gap-1.5 text-purple-400 hover:bg-purple-500/10"
                        >
                          <Bot className="w-3.5 h-3.5" />
                          <span>Copilot</span>
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
