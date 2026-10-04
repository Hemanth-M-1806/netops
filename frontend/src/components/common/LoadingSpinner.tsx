import React from 'react'
import { cn } from '@/utils/formatters'

export const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg'; className?: string; label?: string }> = ({
  size = 'md',
  className,
  label,
}) => {
  const sizeMap = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-2',
    lg: 'w-12 h-12 border-3',
  }

  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 p-8', className)}>
      <div
        className={cn(
          'rounded-full border-cyan-500/20 border-t-cyan-400 animate-spin',
          sizeMap[size]
        )}
      />
      {label && <p className="text-xs text-slate-400 font-mono tracking-wide">{label}</p>}
    </div>
  )
}
