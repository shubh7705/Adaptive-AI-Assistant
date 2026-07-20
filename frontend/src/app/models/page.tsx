'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { Database, Plus, Eye, Key, CheckCircle2, XCircle, X, Loader2 } from 'lucide-react'
import { useState, useEffect } from 'react'

interface Model {
  id: string
  name: string
  provider: string
  cost_per_1k_tokens: number
  supports_tools: boolean
  supports_vision: boolean
  is_active: boolean
}

export default function ModelsRegistry() {
  const [models, setModels] = useState<Model[]>([])
  const [isLoading, setIsLoading] = useState(true)
  
  // Add Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isAdding, setIsAdding] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  
  // Form State
  const [formData, setFormData] = useState({
    name: '',
    provider: 'openrouter',
    cost_per_1k_tokens: 0,
    supports_vision: false,
    supports_tools: false
  })

  const fetchModels = () => {
    fetch('http://127.0.0.1:8000/api/v1/registry/')
      .then(res => res.json())
      .then(data => {
        setModels(data)
        setIsLoading(false)
      })
      .catch(err => {
        setModels([])
        setIsLoading(false)
      })
  }

  useEffect(() => {
    fetchModels()
  }, [])

  const handleAddModel = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsAdding(true)
    setErrorMsg('')
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/registry/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Assuming basic role simulation for admin based on your auth setup
          'Authorization': 'Bearer admin_token_simulation' 
        },
        body: JSON.stringify({
          ...formData,
          is_active: true,
          supports_streaming: true
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to add model')
      }

      // Success
      setIsAddModalOpen(false)
      setFormData({
        name: '', provider: 'openrouter', cost_per_1k_tokens: 0, supports_vision: false, supports_tools: false
      })
      fetchModels() // Refresh list
    } catch (err: any) {
      setErrorMsg(err.message)
    } finally {
      setIsAdding(false)
    }
  }

  return (
    <div className="space-y-8 pb-10">
      <div className="flex items-center justify-between">
        <div>
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-bold tracking-tight text-white mb-2"
          >
            Model Registry
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-white/60"
          >
            Manage active LLMs, API keys, and routing capabilities.
          </motion.p>
        </div>
        <motion.button 
          onClick={() => setIsAddModalOpen(true)}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-white font-medium transition-colors shadow-[0_0_15px_rgba(252,128,255,0.3)]"
        >
          <Plus className="h-4 w-4" />
          Add Model
        </motion.button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-panel rounded-2xl overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-white/80">
            <thead className="text-xs uppercase bg-white/5 border-b border-white/10 text-white">
              <tr>
                <th scope="col" className="px-6 py-4">Model Name</th>
                <th scope="col" className="px-6 py-4">Provider</th>
                <th scope="col" className="px-6 py-4">Cost / 1k (USD)</th>
                <th scope="col" className="px-6 py-4 text-center">Tools</th>
                <th scope="col" className="px-6 py-4 text-center">Vision</th>
                <th scope="col" className="px-6 py-4">Status</th>
                <th scope="col" className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {models.map((model, idx) => (
                <motion.tr 
                  key={model.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + (idx * 0.05) }}
                  className="hover:bg-white/5 transition-colors group"
                >
                  <td className="px-6 py-4 font-medium text-white flex items-center gap-3">
                    <div className="p-1.5 bg-white/10 rounded-md group-hover:bg-primary/20 group-hover:text-primary transition-colors">
                      <Database className="h-4 w-4" />
                    </div>
                    {model.name}
                  </td>
                  <td className="px-6 py-4 capitalize">{model.provider}</td>
                  <td className="px-6 py-4">${model.cost_per_1k_tokens.toFixed(4)}</td>
                  <td className="px-6 py-4 text-center">
                    {model.supports_tools ? <CheckCircle2 className="h-4 w-4 text-emerald-400 mx-auto" /> : <XCircle className="h-4 w-4 text-red-400/50 mx-auto" />}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {model.supports_vision ? <CheckCircle2 className="h-4 w-4 text-emerald-400 mx-auto" /> : <XCircle className="h-4 w-4 text-red-400/50 mx-auto" />}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 text-xs font-medium rounded-full border ${model.is_active ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-white/5 border-white/10 text-white/50'}`}>
                      {model.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button className="p-1.5 text-white/50 hover:text-white hover:bg-white/10 rounded-md transition-colors">
                        <Key className="h-4 w-4" />
                      </button>
                      <button className="p-1.5 text-white/50 hover:text-white hover:bg-white/10 rounded-md transition-colors">
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Add Model Modal */}
      <AnimatePresence>
        {isAddModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-panel w-full max-w-md rounded-2xl p-6 shadow-2xl border border-white/10"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-white">Add New Model</h2>
                <button onClick={() => setIsAddModalOpen(false)} className="text-white/50 hover:text-white transition-colors">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleAddModel} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-1">Model ID / Name</label>
                  <input 
                    type="text" 
                    required
                    placeholder="e.g., meta-llama/llama-3-8b-instruct"
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                  />
                  <p className="text-xs text-white/40 mt-1">The exact model ID used by the provider API.</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-1">Provider</label>
                  <select 
                    className="w-full bg-[#111111] border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-primary/50 transition-all"
                    value={formData.provider}
                    onChange={(e) => setFormData({...formData, provider: e.target.value})}
                  >
                    <option value="openrouter">OpenRouter</option>
                    <option value="groq">Groq</option>
                    <option value="google">Google</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-1">Cost per 1k Tokens (USD)</label>
                  <input 
                    type="number" 
                    step="0.0001"
                    min="0"
                    required
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                    value={formData.cost_per_1k_tokens}
                    onChange={(e) => setFormData({...formData, cost_per_1k_tokens: parseFloat(e.target.value) || 0})}
                  />
                </div>

                <div className="flex gap-6 pt-2">
                  <label className="flex items-center gap-2 text-sm text-white/80 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="rounded border-white/20 bg-black/40 text-primary focus:ring-primary/50"
                      checked={formData.supports_vision}
                      onChange={(e) => setFormData({...formData, supports_vision: e.target.checked})}
                    />
                    Supports Vision
                  </label>
                  <label className="flex items-center gap-2 text-sm text-white/80 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="rounded border-white/20 bg-black/40 text-primary focus:ring-primary/50"
                      checked={formData.supports_tools}
                      onChange={(e) => setFormData({...formData, supports_tools: e.target.checked})}
                    />
                    Supports Tools
                  </label>
                </div>

                {errorMsg && (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                    {errorMsg}
                  </div>
                )}

                <div className="pt-4 flex gap-3">
                  <button 
                    type="button"
                    onClick={() => setIsAddModalOpen(false)}
                    className="flex-1 px-4 py-2.5 rounded-lg border border-white/10 text-white/70 hover:bg-white/5 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    disabled={isAdding}
                    className="flex-1 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-white font-medium transition-colors shadow-[0_0_15px_rgba(252,128,255,0.3)] disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
                  >
                    {isAdding ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Validating...
                      </>
                    ) : (
                      'Verify & Add'
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
