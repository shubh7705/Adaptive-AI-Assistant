'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
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
  id: string;
  name: string;
  provider: string;
  description: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I am ModelRouter AI. How can I help you today? I'll automatically route your request to the best model based on complexity."
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
  
  const DEFAULT_MODELS: RegistryModel[] = [
    {
      id: "google/gemini-2.5-flash",
      name: "Gemini 2.5 Flash",
      provider: "google",
      description: "Fast multimodal model for reasoning, writing, and general tasks.",
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
      description: "Multimodal vision-language free model on OpenRouter.",
    },
  ]

  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
        const headers: Record<string, string> = {}
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        }
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
        if (DEFAULT_MODELS.length > 0) {
          setSelectedModelId(DEFAULT_MODELS[0].id)
        }
      } catch (e) {
        console.warn("Backend registry endpoint unreachable, using default models list:", e)
        setAvailableModels(DEFAULT_MODELS)
        if (DEFAULT_MODELS.length > 0) {
          setSelectedModelId(DEFAULT_MODELS[0].id)
        }
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

    // Setup the placeholder for the streaming response
    const assistantId = crypto.randomUUID()
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', content: '', isStreaming: true }])

    const payload: { query: string; session_id: string; manual_model_id?: string } = { query: input, session_id: 'ui_session' }
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
        throw new Error('API Error')
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
        } catch (error) {
          console.error("SSE parse error", error, data)
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
        console.log("Streaming stopped by user")
        return
      }
      setMessages(prev => prev.map(msg => 
        msg.id === assistantId ? { ...msg, content: 'Error connecting to ModelRouter AI API.' } : msg
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
      <div className="flex items-center justify-between mb-3">
        <div>
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-xl font-bold tracking-tight text-white mb-1"
          >
            Agent Workspace
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-white/60 text-sm hidden md:block"
          >
            Interact with the dynamic multi-model orchestration layer.
          </motion.p>
        </div>
        <motion.div 
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
          className="flex items-center gap-3"
        >
          {/* Toggle Auto Routing */}
          <button 
            type="button"
            role="switch"
            aria-checked={autoRouting}
            aria-label="Toggle auto-routing"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/20 border border-white/10 text-white cursor-pointer hover:bg-white/5 transition-colors" 
            onClick={() => setAutoRouting(!autoRouting)}
          >
            <div className={cn("w-8 h-4 rounded-full p-0.5 transition-colors", autoRouting ? "bg-primary" : "bg-white/20")}>
              <motion.div 
                layout
                className="w-3 h-3 bg-white rounded-full shadow-sm"
                animate={{ x: autoRouting ? 16 : 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            </div>
            <span className="text-xs font-medium">{autoRouting ? 'Auto-Routing On' : 'Manual Mode'}</span>
          </button>
          
          {/* Manual Model Selector */}
          {!autoRouting && (
            <select 
              aria-label="Select model for manual routing" 
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="bg-black/40 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-primary/50 w-48"
            >
              {availableModels.map(m => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.provider})
                </option>
              ))}
            </select>
          )}
        </motion.div>
      </div>

      {/* Chat Area */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="flex-1 glass-panel rounded-2xl flex flex-col overflow-hidden relative"
      >
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={cn(
                  "flex gap-3 max-w-[95%]",
                  message.role === 'user' ? "ml-auto flex-row-reverse" : ""
                )}
              >
                <div className={cn(
                  "flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center border",
                  message.role === 'user' 
                    ? "bg-secondary border-white/10" 
                    : "bg-gradient-to-br from-primary to-accent border-white/20 shadow-[0_0_15px_rgba(252,128,255,0.3)]"
                )}>
                  {message.role === 'user' ? <User className="h-4 w-4 text-white/80" /> : <Cpu className="h-4 w-4 text-white" />}
                </div>
                
                <div className={cn(
                  "px-4 py-3 rounded-2xl text-[14.5px] leading-relaxed",
                  message.role === 'user'
                    ? "bg-primary text-white rounded-tr-sm"
                    : "bg-white/5 border border-white/10 text-white/90 rounded-tl-sm prose prose-sm prose-invert max-w-none"
                )}>
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <div className="relative">
                      {message.model && (
                        <div className="mb-3 pb-3 border-b border-white/10 flex items-center gap-1.5 text-[11px] text-white/40 font-medium">
                          <Sparkles className="h-3 w-3" />
                          Generated by {message.model}
                        </div>
                      )}
                      <ReactMarkdown>
                        {message.content + (message.isStreaming ? ' ▍' : '')}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-3 border-t border-white/10 bg-black/20">
          <form onSubmit={handleSubmit} className="relative flex items-end">
            <textarea
              aria-label="Chat message input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything... ModelRouter will handle the rest."
              rows={Math.max(1, Math.min(5, input.split('\n').length))}
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-4 pr-12 py-3 text-[14.5px] text-white placeholder-white/40 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all resize-none overflow-y-auto min-h-[48px] max-h-[150px]"
              disabled={isTyping}
            />
            {isTyping ? (
              <button
                type="button"
                onClick={stopStreaming}
                className="absolute right-2 bottom-2 p-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
                title="Stop Generating"
              >
                <Square className="h-5 w-5 fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="absolute right-2 bottom-2 p-2 bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-white rounded-lg transition-colors"
              >
                <Send className="h-5 w-5" />
              </button>
            )}
          </form>
        </div>
      </motion.div>
    </div>
  )
}
