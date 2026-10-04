import React from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import { MetricSample } from '@/types'
import { formatBytes } from '@/utils/formatters'

interface TrafficChartProps {
  metrics: MetricSample[]
  title?: string
}

export const TrafficChart: React.FC<TrafficChartProps> = ({
  metrics,
  title = 'Network Throughput (RX / TX)',
}) => {
  // Format data for chart
  const data = metrics.slice(-25).map((m) => {
    const timeStr = m.measured_at
      ? new Date(m.measured_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      : ''
    return {
      time: timeStr,
      rx: m.rx_bytes,
      tx: m.tx_bytes,
      drops: m.packet_drops,
      errors: m.errors,
    }
  })

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-xs font-mono font-semibold uppercase text-slate-300">
          {title}
        </h4>
        <div className="flex items-center gap-4 text-[11px] font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-cyan-400" />
            <span className="text-slate-400">RX Traffic</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-purple-400" />
            <span className="text-slate-400">TX Traffic</span>
          </div>
        </div>
      </div>

      <div className="flex-1 w-full min-h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="rxGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="txGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#c084fc" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#c084fc" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="time"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            />
            <YAxis
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickFormatter={(val) => formatBytes(val)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                fontSize: '11px',
                fontFamily: 'monospace',
              }}
              formatter={(value: any, name: any) => [
                formatBytes(Number(value) || 0),
                name === 'rx' ? 'RX Inbound' : 'TX Outbound',
              ]}
            />
            <Area
              type="monotone"
              dataKey="rx"
              stroke="#06b6d4"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#rxGradient)"
            />
            <Area
              type="monotone"
              dataKey="tx"
              stroke="#c084fc"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#txGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
