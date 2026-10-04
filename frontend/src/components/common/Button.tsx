import React from 'react'
import { cn } from '@/utils/formatters'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, disabled, children, ...props }, ref) => {
    const variantStyles = {
      primary:
        'bg-cyan-500 hover:bg-cyan-400 text-surface-950 font-semibold shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:shadow-[0_0_20px_rgba(6,182,212,0.5)] active:translate-y-px',
      secondary:
        'bg-surface-800 hover:bg-surface-700 text-slate-200 border border-white/10 hover:border-white/20',
      danger:
        'bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 hover:border-rose-500/50',
      ghost:
        'bg-transparent hover:bg-white/5 text-slate-400 hover:text-slate-100',
      outline:
        'bg-transparent border border-white/20 hover:border-white/40 text-slate-200 hover:bg-white/5',
    }

    const sizeStyles = {
      sm: 'text-xs px-2.5 py-1.5 rounded-lg',
      md: 'text-sm px-3.5 py-2 rounded-lg',
      lg: 'text-base px-5 py-2.5 rounded-xl',
    }

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center gap-2 font-medium transition-all duration-150 select-none disabled:opacity-50 disabled:pointer-events-none cursor-pointer',
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading && (
          <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
