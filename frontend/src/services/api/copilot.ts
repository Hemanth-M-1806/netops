import { apiClient } from './client'
import type { CopilotRequest, CopilotResponse, ChatMessage } from '@/types'

export const copilotApi = {
  chat: async (request: CopilotRequest): Promise<CopilotResponse> => {
    const { data } = await apiClient.post<CopilotResponse>('/copilot/chat', request)
    return data
  },

  getHistory: async (sessionId: string, limit = 50): Promise<ChatMessage[]> => {
    const { data } = await apiClient.get<ChatMessage[]>(
      `/copilot/history/${sessionId}`,
      { params: { limit } }
    )
    return data
  },
}
