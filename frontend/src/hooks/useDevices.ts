import { useQuery } from '@tanstack/react-query'
import { devicesApi } from '@/services/api'
import { POLLING_INTERVALS } from '@/utils/constants'

export function useDevices(params?: { status?: string; device_type?: string; limit?: number }) {
  return useQuery({
    queryKey: ['devices', params],
    queryFn: () => devicesApi.list(params),
    refetchInterval: POLLING_INTERVALS.DEVICES,
    staleTime: 5000,
  })
}

export function useDevice(id: number | null) {
  return useQuery({
    queryKey: ['device', id],
    queryFn: () => (id ? devicesApi.get(id) : null),
    enabled: !!id,
  })
}

export function useDeviceInterfaces(deviceId: number | null) {
  return useQuery({
    queryKey: ['device-interfaces', deviceId],
    queryFn: () => (deviceId ? devicesApi.getInterfaces(deviceId) : null),
    enabled: !!deviceId,
    refetchInterval: POLLING_INTERVALS.DEVICES,
  })
}
