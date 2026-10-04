import { create } from 'zustand'

interface TopologyState {
  selectedDeviceId: number | null
  hoveredDeviceId: number | null
  selectedInterfaceId: number | null
  viewMode: '3d' | '2d'
  isDrawerOpen: boolean
  cameraResetTrigger: number
  setSelectedDeviceId: (id: number | null) => void
  setHoveredDeviceId: (id: number | null) => void
  setSelectedInterfaceId: (id: number | null) => void
  setViewMode: (mode: '3d' | '2d') => void
  setIsDrawerOpen: (open: boolean) => void
  resetCamera: () => void
  selectDevice: (id: number) => void
  closeDrawer: () => void
}

export const useTopologyStore = create<TopologyState>((set) => ({
  selectedDeviceId: null,
  hoveredDeviceId: null,
  selectedInterfaceId: null,
  viewMode: '3d',
  isDrawerOpen: false,
  cameraResetTrigger: 0,

  setSelectedDeviceId: (id) => set({ selectedDeviceId: id }),
  setHoveredDeviceId: (id) => set({ hoveredDeviceId: id }),
  setSelectedInterfaceId: (id) => set({ selectedInterfaceId: id }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setIsDrawerOpen: (open) => set({ isDrawerOpen: open }),
  resetCamera: () => set((state) => ({ cameraResetTrigger: state.cameraResetTrigger + 1 })),
  selectDevice: (id) => set({ selectedDeviceId: id, isDrawerOpen: true }),
  closeDrawer: () => set({ isDrawerOpen: false, selectedDeviceId: null, selectedInterfaceId: null }),
}))
