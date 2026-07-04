'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Sparkles, Cpu, Settings2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const apiHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
        const res = await fetch(`http://${apiHost}:8000/api/v1/registry/`, {
          headers: {
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBtb2RlbHJvdXRlci5haSIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTgxNDQxNTQzNX0.Sz_cxtjdtROdCIH7StnYN_rI70G0Blaxc0zaYgUu15k'
          }
        })
        if (res.ok) {
          const data = await res.json()
          setAvailableModels(data)
          if (data.length > 0) {
            setSelectedModelId(data[0].id)
          }
        }
      } catch (e) {
        console.error("Failed to fetch models", e)
      }
    }
    fetchModels()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isTyping) return

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    // Setup the placeholder for the streaming response
    const assistantId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', content: '', isStreaming: true }])

    const payload: any = { query: input, session_id: 'ui_session' }
    if (!autoRouting && selectedModelId) {
      payload.manual_model_id = selectedModelId
    }

    try {
      const apiHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
      const response = await fetch(`http://${apiHost}:8000/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBtb2RlbHJvdXRlci5haSIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTgxNDQxNTQzNX0.Sz_cxtjdtROdCIH7StnYN_rI70G0Blaxc0zaYgUu15k'
        },
        body: JSON.stringify(payload)
      })
      
      if (!response.ok || !response.body) {
        throw new Error('API Error')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let currentContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        // Process SSE lines (data: ...)
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            
            try {
              const parsed = JSON.parse(data)
              if (parsed.model) {
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantId ? { ...msg, model: parsed.model } : msg
                ))
              }
              if (parsed.token) {
                currentContent += parsed.token
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantId ? { ...msg, content: currentContent } : msg
                ))
              }
              if (parsed.error) {
                currentContent += `\n\n**Error:** ${parsed.error}`
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantId ? { ...msg, content: currentContent } : msg
                ))
              }
            } catch (e) {
              console.error("SSE parse error", e, data)
            }
          }
        }
      }
    } catch (error) {
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
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/20 border border-white/10 text-white cursor-pointer hover:bg-white/5 transition-colors" onClick={() => setAutoRouting(!autoRouting)}>
            <div className={cn("w-8 h-4 rounded-full p-0.5 transition-colors", autoRouting ? "bg-primary" : "bg-white/20")}>
              <motion.div 
                layout
                className="w-3 h-3 bg-white rounded-full shadow-sm"
                animate={{ x: autoRouting ? 16 : 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            </div>
            <span className="text-xs font-medium">{autoRouting ? 'Auto-Routing On' : 'Manual Mode'}</span>
          </div>
          
          {/* Manual Model Selector */}
          {!autoRouting && (
            <select 
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
          <form onSubmit={handleSubmit} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything... ModelRouter will handle the rest."
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-4 pr-12 py-3 text-[14.5px] text-white placeholder-white/40 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="absolute right-2 p-2 bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-white rounded-lg transition-colors"
            >
              <Send className="h-5 w-5" />
            </button>
          </form>
        </div>
      </motion.div>
    </div>
  )
}
