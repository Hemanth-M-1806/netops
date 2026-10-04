import React from 'react'
import { Card } from '@/components/common/Card'
import { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: string
  trendPositive?: boolean
  icon: LucideIcon
  iconColor?: string
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendPositive,
  icon: Icon,
  iconColor = 'text-cyan-400',
}) => {
  return (
    <Card className="flex items-start justify-between p-5 relative overflow-hidden group">
      <div>
        <p className="text-[11px] font-mono uppercase text-slate-400 font-semibold tracking-wider">
          {title}
        </p>
        <div className="mt-2 text-2xl font-bold font-mono text-white tracking-tight">
          {value}
        </div>
        {(subtitle || trend) && (
          <div className="mt-1 flex items-center gap-2 text-xs">
            {trend && (
              <span
                className={`font-mono font-medium ${
                  trendPositive ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {trend}
              </span>
            )}
            {subtitle && <span className="text-slate-500 font-mono">{subtitle}</span>}
          </div>
        )}
      </div>

      <div className={`p-3 rounded-xl bg-surface-900 border border-white/10 ${iconColor} group-hover:scale-110 transition-transform`}>
        <Icon className="w-5 h-5" />
      </div>
    </Card>
  )
}
