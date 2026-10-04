import { useMutation, useQuery } from '@tanstack/react-query'
import { copilotApi } from '@/services/api'
import { CopilotRequest } from '@/types'

export function useCopilotChat() {
  return useMutation({
    mutationFn: (request: CopilotRequest) => copilotApi.chat(request),
  })
}

export function useCopilotHistory(sessionId: string) {
  return useQuery({
    queryKey: ['copilot-history', sessionId],
    queryFn: () => copilotApi.getHistory(sessionId),
    enabled: !!sessionId,
  })
}
