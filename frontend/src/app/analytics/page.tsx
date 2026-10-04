'use client'

import { useState, useEffect } from 'react'
import { Activity, DollarSign, Zap, Database, TrendingUp, BarChart3, Loader2, type LucideIcon } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts'

export default function AnalyticsDashboard() {
  const [stats, setStats] = useState<Array<{ name: string; value: string; change: string; icon: LucideIcon; color: string }>>([])
  const [usageData, setUsageData] = useState<Array<{ time: string; tokens: number; cost: number }>>([])
  const [providerData, setProviderData] = useState<Array<{ provider: string; cost: number }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
        const headers: Record<string, string> = {}
        if (token) headers['Authorization'] = `Bearer ${token}`

        const [summaryRes, timeSeriesRes, providerRes] = await Promise.all([
          fetch(`${apiUrl}/api/v1/analytics/summary`, { headers }),
          fetch(`${apiUrl}/api/v1/analytics/time-series`, { headers }),
          fetch(`${apiUrl}/api/v1/analytics/cost-by-provider`, { headers })
        ])

        if (!summaryRes.ok || !timeSeriesRes.ok || !providerRes.ok) throw new Error('Analytics request failed')
        const summaryData: { total_tokens?: number; total_cost_usd?: number; cache_hit_rate?: number; avg_latency_ms?: number } = await summaryRes.json()
        const timeSeriesData: Array<{ time: string; tokens: number; cost: number }> = await timeSeriesRes.json()
        const providerJson: Array<{ provider: string; cost: number }> = await providerRes.json()

        setStats([
          { name: 'Total Tokens', value: (summaryData.total_tokens ?? 0).toLocaleString(), change: '', icon: Database, color: 'text-blue-400' },
          { name: 'Estimated Cost', value: `$${(summaryData.total_cost_usd ?? 0).toFixed(4)}`, change: '', icon: DollarSign, color: 'text-emerald-400' },
          { name: 'Cache Hit Rate', value: `${(summaryData.cache_hit_rate ?? 0).toFixed(1)}%`, change: '', icon: Zap, color: 'text-amber-400' },
          { name: 'Avg Latency', value: `${(summaryData.avg_latency_ms ?? 0).toFixed(0)}ms`, change: '', icon: Activity, color: 'text-blue-400' },
        ])

        setUsageData(timeSeriesData)
        setProviderData(providerJson)
      } catch (err) {
        console.error("Failed to fetch analytics:", err)
        setError("Failed to load analytics data. Please check your connection.")
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [])

  const CHART_COLORS = ['#2563eb', '#3b82f6', '#60a5fa', '#10b981', '#f59e0b']

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center min-h-[300px]">
        <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full w-full items-center justify-center min-h-[300px]">
        <div className="text-center panel p-6 max-w-md">
          <p className="text-red-400 text-sm mb-3">{error}</p>
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
      <div className="border-b border-zinc-800 pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">
          Analytics and Cost
        </h1>
        <p className="text-sm text-zinc-400 mt-1">
          Historical request metrics, token utilization, and provider expenses.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="panel p-4 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-zinc-400">{stat.name}</span>
              <div className="p-1.5 bg-zinc-800/80 rounded-md">
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </div>
            <div>
              <div className="text-2xl font-semibold tracking-tight text-zinc-100">{stat.value}</div>
              {stat.change && (
                <span className="text-xs font-medium text-emerald-400 mt-1 inline-block">
                  {stat.change}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Charts Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Token Usage Chart */}
        <div className="panel p-5 lg:col-span-2 flex flex-col h-[380px]">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-zinc-800/80">
            <TrendingUp className="h-4 w-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-zinc-100">Token Usage Over Time</h2>
          </div>
          <div className="flex-1 w-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={usageData} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 2" stroke="#27272a" vertical={false} />
                <XAxis dataKey="time" stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: '#18181b',
                    border: '1px solid #27272a',
                    borderRadius: '6px',
                    color: '#f4f4f5',
                    fontSize: '12px'
                  }}
                  itemStyle={{ color: '#f4f4f5' }}
                />
                <Area
                  type="monotone"
                  dataKey="tokens"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fill="#2563eb"
                  fillOpacity={0.12}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cost by Provider Chart */}
        <div className="panel p-5 flex flex-col h-[380px]">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-zinc-800/80">
            <BarChart3 className="h-4 w-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-zinc-100">Cost by Provider</h2>
          </div>
          <div className="flex-1 w-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={providerData} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 2" stroke="#27272a" vertical={false} />
                <XAxis dataKey="provider" stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: '#18181b',
                    border: '1px solid #27272a',
                    borderRadius: '6px',
                    color: '#f4f4f5',
                    fontSize: '12px'
                  }}
                  itemStyle={{ color: '#f4f4f5' }}
                  cursor={{ fill: 'rgba(255, 255, 255, 0.03)' }}
                />
                <Bar dataKey="cost" radius={[2, 2, 0, 0]}>
                  {providerData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
