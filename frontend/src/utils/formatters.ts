import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { Severity, DeviceStatus } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatBytes(bytes: number, decimals = 1): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

export function formatBitsPerSecond(bps: number, decimals = 1): string {
  if (bps === 0) return '0 bps'
  const k = 1000
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']
  const i = Math.floor(Math.log(bps) / Math.log(k))
  return `${parseFloat((bps / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

export function formatTimeAgo(isoString: string): string {
  try {
    const date = new Date(isoString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 5) return 'just now'
    if (seconds < 60) return `${seconds}s ago`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ago`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  } catch {
    return isoString
  }
}

export function getSeverityColor(severity: Severity): {
  bg: string
  text: string
  border: string
  hex: string
} {
  switch (severity) {
    case 'CRITICAL':
      return {
        bg: 'bg-rose-500/10',
        text: 'text-rose-400',
        border: 'border-rose-500/30',
        hex: '#f43f5e',
      }
    case 'HIGH':
      return {
        bg: 'bg-orange-500/10',
        text: 'text-orange-400',
        border: 'border-orange-500/30',
        hex: '#f97316',
      }
    case 'MEDIUM':
      return {
        bg: 'bg-amber-500/10',
        text: 'text-amber-400',
        border: 'border-amber-500/30',
        hex: '#f59e0b',
      }
    case 'LOW':
    default:
      return {
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/30',
        hex: '#10b981',
      }
  }
}

export function getDeviceStatusColor(status: DeviceStatus): {
  dot: string
  text: string
  badge: string
  hex: string
} {
  switch (status) {
    case 'UP':
      return {
        dot: 'bg-emerald-400 shadow-[0_0_8px_#34d399]',
        text: 'text-emerald-400',
        badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
        hex: '#10b981',
      }
    case 'CRITICAL':
      return {
        dot: 'bg-rose-500 shadow-[0_0_8px_#f43f5e]',
        text: 'text-rose-400',
        badge: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
        hex: '#f43f5e',
      }
    case 'WARNING':
      return {
        dot: 'bg-amber-400 shadow-[0_0_8px_#fbbf24]',
        text: 'text-amber-400',
        badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
        hex: '#f59e0b',
      }
    case 'DOWN':
      return {
        dot: 'bg-red-600 shadow-[0_0_8px_#dc2626]',
        text: 'text-red-500',
        badge: 'bg-red-500/10 text-red-500 border-red-500/20',
        hex: '#ef4444',
      }
    case 'MAINTENANCE':
    default:
      return {
        dot: 'bg-slate-400',
        text: 'text-slate-400',
        badge: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
        hex: '#64748b',
      }
  }
}
