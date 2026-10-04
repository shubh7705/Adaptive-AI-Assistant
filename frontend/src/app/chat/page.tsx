'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, User, Sparkles, Cpu, Square } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  model?: string
}

interface RegistryModel {
  id: string
  name: string
  provider: string
  description: string
}

const DEFAULT_MODELS: RegistryModel[] = [
  {
    id: "google/gemini-2.5-flash",
    name: "Gemini 2.5 Flash",
    provider: "google",
    description: "Fast model for reasoning and general queries.",
  },
  {
    id: "deepseek/deepseek-chat",
    name: "DeepSeek Chat",
    provider: "openrouter",
    description: "High-performance coding and complex reasoning assistant.",
  },
  {
    id: "inclusionai/ling-3.0-flash-vl:free",
    name: "Ling 3.0 Flash VL (Free)",
    provider: "openrouter",
    description: "Multimodal vision-language free model.",
  },
]

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello. I am Adaptive Chat AI. How can I assist you today? I will route your prompt to the most suitable model based on complexity and task requirements."
    }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [autoRouting, setAutoRouting] = useState(true)
  const [availableModels, setAvailableModels] = useState<RegistryModel[]>([])
  const [selectedModelId, setSelectedModelId] = useState<string>("")

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const rafRef = useRef<number | null>(null)
  const pendingContentRef = useRef<string>('')

  const stopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsTyping(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim() && !isTyping) {
        void handleSubmit(e)
      }
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
        const headers: Record<string, string> = {}
        if (token) headers['Authorization'] = `Bearer ${token}`

        const res = await fetch(`${apiUrl}/api/v1/registry/`, { headers })
        if (res.ok) {
          const data = await res.json()
          if (Array.isArray(data) && data.length > 0) {
            setAvailableModels(data)
            setSelectedModelId(data[0].id)
            return
          }
        }
        setAvailableModels(DEFAULT_MODELS)
        if (DEFAULT_MODELS.length > 0) setSelectedModelId(DEFAULT_MODELS[0].id)
      } catch (err) {
        console.warn("Backend registry endpoint unreachable, using default models:", err)
        setAvailableModels(DEFAULT_MODELS)
        if (DEFAULT_MODELS.length > 0) setSelectedModelId(DEFAULT_MODELS[0].id)
      }
    }
    fetchModels()
  }, [])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement> | React.KeyboardEvent<HTMLTextAreaElement>) => {
    e.preventDefault()
    if (!input.trim() || isTyping) return

    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    abortControllerRef.current = new AbortController()

    const assistantId = crypto.randomUUID()
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', content: '', isStreaming: true }])

    const payload: { query: string; session_id: string; manual_model_id?: string } = {
      query: input,
      session_id: 'ui_session'
    }
    if (!autoRouting && selectedModelId) {
      payload.manual_model_id = selectedModelId
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const authToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
      const response = await fetch(`${apiUrl}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
        },
        body: JSON.stringify(payload),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok || !response.body) {
        throw new Error('API request failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let currentContent = ''
      let eventBuffer = ''

      const processEvent = (event: string) => {
        const dataLine = event.split('\n').find((line) => line.startsWith('data: '))
        if (!dataLine) return
        const data = dataLine.slice(6)
        if (data === '[DONE]') return

        try {
          const parsed = JSON.parse(data)
          if (parsed.model) {
            setMessages(prev => prev.map(msg =>
              msg.id === assistantId ? { ...msg, model: parsed.model } : msg
            ))
          }
          if (parsed.token) {
            currentContent += parsed.token
            pendingContentRef.current = currentContent
            if (!rafRef.current) {
              rafRef.current = requestAnimationFrame(() => {
                const content = pendingContentRef.current
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content } : msg
                ))
                rafRef.current = null
              })
            }
          }
          if (parsed.error) {
            currentContent += `\n\n**Error:** ${parsed.error}`
            setMessages(prev => prev.map(msg =>
              msg.id === assistantId ? { ...msg, content: currentContent } : msg
            ))
          }
        } catch (err) {
          console.error("SSE parse error", err, data)
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        eventBuffer += decoder.decode(value, { stream: true })
        const events = eventBuffer.split('\n\n')
        eventBuffer = events.pop() ?? ''
        for (const event of events) {
          processEvent(event)
        }
      }
      eventBuffer += decoder.decode()
      if (eventBuffer.trim()) processEvent(eventBuffer)
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }
      setMessages(prev => prev.map(msg =>
        msg.id === assistantId ? { ...msg, content: 'Error connecting to Adaptive Chat API.' } : msg
      ))
    } finally {
      setMessages(prev => prev.map(msg =>
        msg.id === assistantId ? { ...msg, isStreaming: false } : msg
      ))
      setIsTyping(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] -mb-8">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
            Agent Workspace
          </h1>
          <p className="text-xs text-zinc-400 hidden sm:block">
            Intelligent multi-model orchestration with real-time streaming.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            role="switch"
            aria-checked={autoRouting}
            onClick={() => setAutoRouting(!autoRouting)}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-medium transition-colors cursor-pointer",
              autoRouting
                ? "bg-blue-950/40 border-blue-800/60 text-blue-300"
                : "bg-zinc-900 border-zinc-700/60 text-zinc-400 hover:text-zinc-200"
            )}
          >
            <span className={cn("w-2 h-2 rounded-sm", autoRouting ? "bg-blue-400" : "bg-zinc-500")} />
            <span>{autoRouting ? 'Auto-Routing Active' : 'Manual Mode'}</span>
          </button>

          {!autoRouting && (
            <select
              aria-label="Select model for manual routing"
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="bg-zinc-900 border border-zinc-700/60 rounded-md px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-blue-500 max-w-[200px]"
            >
              {availableModels.map(m => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.provider})
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Main Chat Box */}
      <div className="panel flex-1 flex flex-col overflow-hidden">
        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3 max-w-[92%]",
                message.role === 'user' ? "ml-auto flex-row-reverse" : ""
              )}
            >
              <div
                className={cn(
                  "shrink-0 h-7 w-7 rounded-md flex items-center justify-center border text-xs",
                  message.role === 'user'
                    ? "bg-zinc-800 border-zinc-700 text-zinc-300"
                    : "bg-blue-600 border-blue-500 text-white"
                )}
              >
                {message.role === 'user' ? <User className="h-3.5 w-3.5" /> : <Cpu className="h-3.5 w-3.5" />}
              </div>

              <div
                className={cn(
                  "px-3.5 py-2.5 rounded-md text-[14px] leading-relaxed",
                  message.role === 'user'
                    ? "bg-blue-600 text-white font-normal"
                    : "bg-[#18181b] border border-zinc-800 text-zinc-200 prose prose-sm prose-invert max-w-none"
                )}
              >
                {message.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <div>
                    {message.model && (
                      <div className="mb-2 pb-2 border-b border-zinc-800 flex items-center gap-1.5 text-[11px] text-zinc-400 font-medium">
                        <Sparkles className="h-3 w-3 text-blue-400" />
                        <span>Routed to {message.model}</span>
                      </div>
                    )}
                    <ReactMarkdown>
                      {message.content + (message.isStreaming ? ' ▍' : '')}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-3 border-t border-zinc-800 bg-[#0d0d0f]">
          <form onSubmit={handleSubmit} className="relative flex items-end">
            <textarea
              aria-label="Chat message input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
              rows={Math.max(1, Math.min(5, input.split('\n').length))}
              className="w-full bg-[#141416] border border-zinc-700/60 rounded-md pl-3.5 pr-12 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors resize-none overflow-y-auto min-h-[44px] max-h-[140px]"
              disabled={isTyping}
            />
            {isTyping ? (
              <button
                type="button"
                onClick={stopStreaming}
                className="absolute right-2 bottom-2 p-1.5 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
                title="Stop Generating"
              >
                <Square className="h-4 w-4 fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="absolute right-2 bottom-2 p-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-md transition-colors"
                title="Send Message"
              >
                <Send className="h-4 w-4" />
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
  )
}
