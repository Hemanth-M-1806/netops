import { useQuery } from '@tanstack/react-query'
import { interfacesApi } from '@/services/api'
import { POLLING_INTERVALS } from '@/utils/constants'

export function useInterfaceMetrics(
  interfaceId: number | null,
  params?: { limit?: number; from_time?: string; to_time?: string }
) {
  return useQuery({
    queryKey: ['interface-metrics', interfaceId, params],
    queryFn: () => (interfaceId ? interfacesApi.getMetrics(interfaceId, params) : null),
    enabled: !!interfaceId,
    refetchInterval: POLLING_INTERVALS.METRICS,
  })
}

export function useInterfaceScore(interfaceId: number | null) {
  return useQuery({
    queryKey: ['interface-score', interfaceId],
    queryFn: () => (interfaceId ? interfacesApi.getScore(interfaceId) : null),
    enabled: !!interfaceId,
    refetchInterval: POLLING_INTERVALS.METRICS,
  })
}
