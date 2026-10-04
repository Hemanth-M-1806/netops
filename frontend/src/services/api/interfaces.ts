import { apiClient } from './client'
import type {
  NetworkInterface,
  MetricListResponse,
  RiskScore,
} from '@/types'

export const interfacesApi = {
  get: async (id: number): Promise<NetworkInterface> => {
    const { data } = await apiClient.get<NetworkInterface>(`/interfaces/${id}`)
    return data
  },

  getMetrics: async (
    id: number,
    params?: {
      from_time?: string
      to_time?: string
      limit?: number
    }
  ): Promise<MetricListResponse> => {
    const { data } = await apiClient.get<MetricListResponse>(
      `/interfaces/${id}/metrics`,
      { params }
    )
    return data
  },

  getScore: async (id: number): Promise<RiskScore> => {
    const { data } = await apiClient.get<RiskScore>(`/interfaces/${id}/score`)
    return data
  },
}
