import { create } from 'zustand'
import { ChatMessage } from '@/types'

function generateSessionId(): string {
  return 'sess_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now().toString(36)
}

interface CopilotState {
  sessionId: string
  messages: ChatMessage[]
  targetDeviceId: number | null
  targetInterfaceId: number | null
  isStreaming: boolean
  setSessionId: (id: string) => void
  setTargetDeviceId: (id: number | null) => void
  setTargetInterfaceId: (id: number | null) => void
  addMessage: (message: ChatMessage) => void
  setMessages: (messages: ChatMessage[]) => void
  setIsStreaming: (loading: boolean) => void
  clearChat: () => void
  startNewSession: () => void
}

export const useCopilotStore = create<CopilotState>((set) => ({
  sessionId: localStorage.getItem('netops_copilot_session') || (() => {
    const newId = generateSessionId()
    localStorage.setItem('netops_copilot_session', newId)
    return newId
  })(),
  messages: [],
  targetDeviceId: null,
  targetInterfaceId: null,
  isStreaming: false,

  setSessionId: (id) => {
    localStorage.setItem('netops_copilot_session', id)
    set({ sessionId: id })
  },
  setTargetDeviceId: (id) => set({ targetDeviceId: id }),
  setTargetInterfaceId: (id) => set({ targetInterfaceId: id }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setMessages: (messages) => set({ messages }),
  setIsStreaming: (isStreaming) => set({ isStreaming }),
  clearChat: () => set({ messages: [] }),
  startNewSession: () => {
    const newId = generateSessionId()
    localStorage.setItem('netops_copilot_session', newId)
    set({ sessionId: newId, messages: [], targetDeviceId: null, targetInterfaceId: null })
  },
}))
