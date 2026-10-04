import { apiClient } from './client'
import type {
  Device,
  DeviceListResponse,
  InterfaceListResponse,
} from '@/types'

export const devicesApi = {
  list: async (params?: {
    status?: string
    device_type?: string
    limit?: number
    offset?: number
  }): Promise<DeviceListResponse> => {
    const { data } = await apiClient.get<DeviceListResponse>('/devices', { params })
    return data
  },

  get: async (id: number): Promise<Device> => {
    const { data } = await apiClient.get<Device>(`/devices/${id}`)
    return data
  },

  getInterfaces: async (deviceId: number): Promise<InterfaceListResponse> => {
    const { data } = await apiClient.get<InterfaceListResponse>(
      `/devices/${deviceId}/interfaces`
    )
    return data
  },
}
