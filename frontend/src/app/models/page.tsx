'use client'

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
  const [fetchError, setFetchError] = useState<string | null>(null)

  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isAdding, setIsAdding] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const [formData, setFormData] = useState({
    name: '',
    provider: 'openrouter',
    cost_per_1k_tokens: 0,
    supports_vision: false,
    supports_tools: false
  })

  const fetchModels = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${apiUrl}/api/v1/registry/`)
      .then(res => res.json())
      .then(data => {
        setModels(Array.isArray(data) ? data : [])
        setIsLoading(false)
      })
      .catch(err => {
        console.error("Failed to fetch models:", err)
        setModels([])
        setFetchError("Failed to load models. Please check your connection.")
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/registry/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(typeof window !== 'undefined' && localStorage.getItem('auth_token') ? { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` } : {})
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

      setIsAddModalOpen(false)
      setFormData({
        name: '', provider: 'openrouter', cost_per_1k_tokens: 0, supports_vision: false, supports_tools: false
      })
      fetchModels()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to add model')
    } finally {
      setIsAdding(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center min-h-[300px]">
        <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
      </div>
    )
  }

  if (fetchError) {
    return (
      <div className="flex h-full w-full items-center justify-center min-h-[300px]">
        <div className="text-center panel p-6 max-w-md">
          <p className="text-red-400 text-sm mb-3">{fetchError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">
            Model Registry
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Active LLMs, provider configurations, and routing capabilities.
          </p>
        </div>
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium transition-colors self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          Add Model
        </button>
      </div>

      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-zinc-300">
            <thead className="text-[11px] uppercase tracking-wider bg-zinc-900 border-b border-zinc-800 text-zinc-400 font-medium">
              <tr>
                <th scope="col" className="px-5 py-3">Model Name</th>
                <th scope="col" className="px-5 py-3">Provider</th>
                <th scope="col" className="px-5 py-3">Cost / 1k Tokens</th>
                <th scope="col" className="px-5 py-3 text-center">Tools</th>
                <th scope="col" className="px-5 py-3 text-center">Vision</th>
                <th scope="col" className="px-5 py-3">Status</th>
                <th scope="col" className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/80">
              {models.map((model) => (
                <tr
                  key={model.name}
                  className="hover:bg-zinc-900/50 transition-colors"
                >
                  <td className="px-5 py-3 font-medium text-zinc-100 flex items-center gap-2.5">
                    <div className="p-1 bg-zinc-800 rounded text-zinc-400">
                      <Database className="h-3.5 w-3.5" />
                    </div>
                    <span>{model.name}</span>
                  </td>
                  <td className="px-5 py-3 capitalize text-zinc-300">{model.provider}</td>
                  <td className="px-5 py-3 text-zinc-300">${model.cost_per_1k_tokens.toFixed(4)}</td>
                  <td className="px-5 py-3 text-center">
                    {model.supports_tools ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 mx-auto" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5 text-zinc-600 mx-auto" />
                    )}
                  </td>
                  <td className="px-5 py-3 text-center">
                    {model.supports_vision ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 mx-auto" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5 text-zinc-600 mx-auto" />
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 text-[11px] font-medium rounded border ${
                      model.is_active
                        ? 'bg-emerald-950/40 border-emerald-800/50 text-emerald-400'
                        : 'bg-zinc-900 border-zinc-800 text-zinc-500'
                    }`}>
                      {model.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        className="p-1 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded transition-colors"
                        aria-label="Manage API key"
                        title="Manage Key"
                      >
                        <Key className="h-3.5 w-3.5" />
                      </button>
                      <button
                        className="p-1 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded transition-colors"
                        aria-label="View model details"
                        title="View Details"
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Model Modal */}
      {isAddModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-model-title"
          onKeyDown={(e) => { if (e.key === 'Escape') setIsAddModalOpen(false) }}
        >
          <div className="panel w-full max-w-md p-5 bg-[#141416] border border-zinc-700 shadow-xl">
            <div className="flex justify-between items-center mb-4 pb-3 border-b border-zinc-800">
              <h2 id="add-model-title" className="text-base font-semibold text-zinc-100">
                Add Model to Registry
              </h2>
              <button
                onClick={() => setIsAddModalOpen(false)}
                aria-label="Close modal"
                className="text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleAddModel} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  Model ID / Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. meta-llama/llama-3-8b-instruct"
                  className="w-full panel-input px-3 py-2 text-xs"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
                <p className="text-[11px] text-zinc-500 mt-1">Exact model identifier accepted by the provider.</p>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  Provider
                </label>
                <select
                  className="w-full panel-input px-3 py-2 text-xs"
                  value={formData.provider}
                  onChange={(e) => setFormData({...formData, provider: e.target.value})}
                >
                  <option value="openrouter">OpenRouter</option>
                  <option value="groq">Groq</option>
                  <option value="google">Google</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  Cost per 1k Tokens (USD)
                </label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  required
                  className="w-full panel-input px-3 py-2 text-xs"
                  value={formData.cost_per_1k_tokens}
                  onChange={(e) => setFormData({...formData, cost_per_1k_tokens: parseFloat(e.target.value) || 0})}
                />
              </div>

              <div className="flex gap-6 pt-1">
                <label className="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer">
                  <input
                    type="checkbox"
                    className="rounded border-zinc-700 bg-zinc-900 text-blue-600 focus:ring-blue-500"
                    checked={formData.supports_vision}
                    onChange={(e) => setFormData({...formData, supports_vision: e.target.checked})}
                  />
                  <span>Supports Vision</span>
                </label>
                <label className="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer">
                  <input
                    type="checkbox"
                    className="rounded border-zinc-700 bg-zinc-900 text-blue-600 focus:ring-blue-500"
                    checked={formData.supports_tools}
                    onChange={(e) => setFormData({...formData, supports_tools: e.target.checked})}
                  />
                  <span>Supports Tools</span>
                </label>
              </div>

              {errorMsg && (
                <div className="p-2.5 bg-red-950/40 border border-red-800/60 rounded text-red-400 text-xs">
                  {errorMsg}
                </div>
              )}

              <div className="pt-3 flex gap-2 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="flex-1 px-3 py-2 rounded-md border border-zinc-700 text-zinc-300 hover:bg-zinc-800 text-xs font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isAdding}
                  className="flex-1 px-3 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-1.5"
                >
                  {isAdding ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Validating...</span>
                    </>
                  ) : (
                    'Save Model'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
