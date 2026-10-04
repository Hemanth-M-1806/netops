import { apiClient } from './client'
import type { AlertListResponse, Alert } from '@/types'

export const alertsApi = {
  list: async (params?: {
    resolved?: boolean
    severity?: string
    device_id?: number
    limit?: number
    offset?: number
  }): Promise<AlertListResponse> => {
    const { data } = await apiClient.get<AlertListResponse>('/alerts', { params })
    return data
  },

  resolve: async (id: number): Promise<Alert> => {
    const { data } = await apiClient.patch<Alert>(`/alerts/${id}/resolve`)
    return data
  },
}
