import React from 'react'
import { cn } from '@/utils/formatters'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: boolean
}

export const Card: React.FC<CardProps> = ({ children, className, glow, ...props }) => {
  return (
    <div
      className={cn(
        'glass-panel rounded-xl border border-white/[0.08] p-5 transition-all duration-200',
        glow && 'hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(6,182,212,0.15)]',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
