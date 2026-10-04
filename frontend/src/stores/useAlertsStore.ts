import { create } from 'zustand'
import { Severity } from '@/types'

interface AlertsFilterState {
  severity: Severity | 'ALL'
  resolved: boolean | null // null = all, false = active only, true = resolved only
  searchQuery: string
  selectedAlertId: number | null
  setSeverity: (severity: Severity | 'ALL') => void
  setResolved: (resolved: boolean | null) => void
  setSearchQuery: (query: string) => void
  setSelectedAlertId: (id: number | null) => void
  resetFilters: () => void
}

export const useAlertsStore = create<AlertsFilterState>((set) => ({
  severity: 'ALL',
  resolved: false, // Default to showing active alerts only
  searchQuery: '',
  selectedAlertId: null,

  setSeverity: (severity) => set({ severity }),
  setResolved: (resolved) => set({ resolved }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  setSelectedAlertId: (id) => set({ selectedAlertId: id }),
  resetFilters: () => set({ severity: 'ALL', resolved: false, searchQuery: '' }),
}))
