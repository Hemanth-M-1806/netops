import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { alertsApi } from '@/services/api'
import { POLLING_INTERVALS } from '@/utils/constants'

export function useAlerts(params?: {
  resolved?: boolean
  severity?: string
  device_id?: number
  limit?: number
}) {
  return useQuery({
    queryKey: ['alerts', params],
    queryFn: () => alertsApi.list(params),
    refetchInterval: POLLING_INTERVALS.ALERTS,
    staleTime: 3000,
  })
}

export function useResolveAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => alertsApi.resolve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}
