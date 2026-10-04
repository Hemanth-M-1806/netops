import React from 'react'
import { Severity } from '@/types'
import { getSeverityColor } from '@/utils/formatters'

interface AlertBadgeProps {
  severity: Severity
  className?: string
}

export const AlertBadge: React.FC<AlertBadgeProps> = ({ severity, className = '' }) => {
  const colors = getSeverityColor(severity)

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md font-mono text-[10px] font-bold uppercase tracking-wider border ${colors.bg} ${colors.text} ${colors.border} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: colors.hex }} />
      {severity}
    </span>
  )
}
