import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, RefreshCw, X, AlertCircle } from 'lucide-react'
import { useCopilotStore } from '@/stores/useCopilotStore'
import { useCopilotChat } from '@/hooks/useCopilot'
import { useDevices } from '@/hooks/useDevices'
import { Button } from '@/components/common/Button'
import { Badge } from '@/components/common/Badge'

const SUGGESTED_PROMPTS = [
  'What are the critical alerts right now?',
  'Analyze traffic patterns and packet drops across core routers.',
  'Is there any interface experiencing high error rates?',
  'Give me an operational summary of CORE-SW1 and CORE-SW2.',
]

export const CopilotChat: React.FC = () => {
  const {
    sessionId,
    messages,
    targetDeviceId,
    targetInterfaceId,
    addMessage,
    startNewSession,
    setTargetDeviceId,
  } = useCopilotStore()

  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatMutation = useCopilotChat()
  const { data: devicesData } = useDevices()

  const selectedDevice = devicesData?.items.find((d) => d.device_id === targetDeviceId)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, chatMutation.isPending])

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input
    if (!query.trim() || chatMutation.isPending) return

    // Append user message locally
    addMessage({
      id: Date.now(),
      session_id: sessionId,
      role: 'user',
      content: query,
      token_count: query.split(' ').length,
      created_at: new Date().toISOString(),
    })

    setInput('')

    try {
      const response = await chatMutation.mutateAsync({
        session_id: sessionId,
        content: query,
        device_id: targetDeviceId || undefined,
        interface_id: targetInterfaceId || undefined,
      })

      addMessage(response.assistant_message)
    } catch (err: any) {
      // The API client normalises backend errors to Error(detail), so surface it.
      const detail =
        typeof err?.message === 'string' && err.message && err.message !== 'Network Error'
          ? err.message
          : null
      addMessage({
        id: Date.now(),
        session_id: sessionId,
        role: 'assistant',
        content: detail
          ? `⚠️ Copilot error: ${detail}`
          : '⚠️ Error connecting to NetOps Copilot service. Please verify that the backend LLM provider is configured.',
        token_count: null,
        created_at: new Date().toISOString(),
      })
    }
  }

  return (
    <div className="flex flex-col h-full bg-surface-950/60 rounded-2xl border border-white/[0.08] overflow-hidden">
      {/* Header bar */}
      <div className="p-4 border-b border-white/[0.08] bg-surface-900/60 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-600 to-cyan-500 flex items-center justify-center shadow-[0_0_12px_rgba(168,85,247,0.4)]">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="font-mono font-bold text-sm text-white flex items-center gap-2">
              NetOps AI Copilot
              <span className="text-[10px] font-normal text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
                RAG Grounded
              </span>
            </h3>
            <p className="text-[11px] text-slate-400 font-mono">
              Live Network Context & Root Cause Analysis
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {selectedDevice && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/30 text-xs font-mono text-cyan-300">
              <span>Scoped to: {selectedDevice.hostname}</span>
              <button
                onClick={() => setTargetDeviceId(null)}
                className="hover:text-white"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={startNewSession}
            title="Start New Session"
            className="text-xs font-mono"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </Button>
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-surface-900 border border-white/10 flex items-center justify-center shadow-inner">
              <Bot className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h4 className="text-white font-mono font-bold text-base">
                How can I assist your network operations today?
              </h4>
              <p className="text-slate-400 text-xs mt-1">
                NetOps Copilot retrieves live telemetry, topology links, and recent ML anomaly scores to answer diagnosis questions.
              </p>
            </div>

            {/* Prompt Suggestion Chips */}
            <div className="w-full space-y-2 pt-2">
              {SUGGESTED_PROMPTS.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(prompt)}
                  className="w-full text-left p-3 rounded-xl bg-surface-900/60 hover:bg-surface-800/80 border border-white/[0.06] hover:border-cyan-500/40 text-xs font-mono text-slate-300 hover:text-white transition-all cursor-pointer shadow-sm"
                >
                  💬 {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-lg bg-surface-800 border border-white/10 flex items-center justify-center shrink-0 mt-1">
                  <Bot className="w-4 h-4 text-cyan-400" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl p-4 text-xs font-sans leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-cyan-500/20 border border-cyan-500/40 text-cyan-50 rounded-tr-none'
                    : 'bg-surface-900 border border-white/10 text-slate-200 rounded-tl-none shadow-lg'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
                <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
                  <span>
                    {new Date(msg.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  {msg.token_count && (
                    <span>{msg.token_count} tokens</span>
                  )}
                </div>
              </div>
              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-cyan-600/30 border border-cyan-500/40 flex items-center justify-center shrink-0 mt-1">
                  <User className="w-4 h-4 text-cyan-300" />
                </div>
              )}
            </div>
          ))
        )}

        {chatMutation.isPending && (
          <div className="flex gap-3 justify-start items-center">
            <div className="w-7 h-7 rounded-lg bg-surface-800 border border-white/10 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-cyan-400 animate-pulse" />
            </div>
            <div className="bg-surface-900 border border-white/10 rounded-2xl rounded-tl-none p-3.5 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.2s]" />
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.4s]" />
              <span className="text-xs font-mono text-slate-400 ml-1">
                Grounding against live MySQL telemetry & topology...
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div className="p-4 border-t border-white/[0.08] bg-surface-900/60">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSend()
          }}
          className="flex items-center gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              selectedDevice
                ? `Ask about ${selectedDevice.hostname}...`
                : 'Ask NetOps Copilot about telemetry, faults, or topologies...'
            }
            className="flex-1 bg-surface-950 border border-white/15 rounded-xl px-4 py-3 text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400/80 transition-colors"
          />
          <Button
            type="submit"
            variant="primary"
            disabled={!input.trim() || chatMutation.isPending}
            className="px-4 py-3"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}
