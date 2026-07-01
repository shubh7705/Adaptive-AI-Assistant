'use client'

import { motion } from 'framer-motion'
import { Database, Plus, Eye, Key, CheckCircle2, XCircle } from 'lucide-react'
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

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/registry/')
      .then(res => res.json())
      .then(data => {
        setModels(data)
        setIsLoading(false)
      })
      .catch(err => {
        // Fallback to empty models if backend is down
        setModels([])
        setIsLoading(false)
      })
  }, [])
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
    </div>
  )
}
