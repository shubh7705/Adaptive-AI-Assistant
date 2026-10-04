'use client'

import { useState, useEffect } from 'react'
import { Activity, Zap, Server, BrainCircuit, BarChart3, Loader2, type LucideIcon } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Array<{ title: string; value: string; change: string; icon: LucideIcon; color: string }>>([])
  const [chartData, setChartData] = useState<Array<{ name: string; count: number }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
        const headers: Record<string, string> = {}
        if (token) headers['Authorization'] = `Bearer ${token}`

        const [summaryRes, distRes] = await Promise.all([
          fetch(`${apiUrl}/api/v1/analytics/summary`, { headers }),
          fetch(`${apiUrl}/api/v1/analytics/routing-distribution`, { headers })
        ])

        if (!summaryRes.ok || !distRes.ok) throw new Error('Analytics request failed')
        const summaryData: { total_requests?: number; cache_hit_rate?: number; avg_latency_ms?: number; total_tokens?: number } = await summaryRes.json()
        const distData: { distribution: Record<string, number> } = await distRes.json()

        setMetrics([
          {
            title: "Total Requests",
            value: (summaryData.total_requests ?? 0).toLocaleString(),
            change: "",
            icon: Activity,
            color: "text-blue-400"
          },
          {
            title: "Cache Hit Rate",
            value: `${(summaryData.cache_hit_rate ?? 0).toFixed(1)}%`,
            change: "",
            icon: Zap,
            color: "text-amber-400"
          },
          {
            title: "Avg Latency",
            value: `${(summaryData.avg_latency_ms ?? 0).toFixed(0)}ms`,
            change: "",
            icon: Server,
            color: "text-emerald-400"
          },
          {
            title: "Total Tokens",
            value: (summaryData.total_tokens ?? 0).toLocaleString(),
            change: "",
            icon: BrainCircuit,
            color: "text-zinc-300"
          },
        ])

        const formattedChartData = Object.entries(distData.distribution).map(([name, count]) => ({
          name: name.split('/').pop() || name,
          count: count
        }))

        setChartData(formattedChartData)
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">
            System Overview
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Real-time routing analytics and model performance metrics.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto px-2.5 py-1 rounded-md bg-emerald-950/40 border border-emerald-800/50 text-emerald-400 text-xs font-medium">
          <span className="w-1.5 h-1.5 rounded-sm bg-emerald-400" />
          <span>System Operational</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => (
          <div
            key={metric.title}
            className="panel p-4 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-zinc-400">{metric.title}</span>
              <metric.icon className={`h-4 w-4 ${metric.color}`} />
            </div>
            <div>
              <div className="text-2xl font-semibold tracking-tight text-zinc-100">{metric.value}</div>
              {metric.change && (
                <span className="text-xs font-medium text-emerald-400 mt-1 inline-block">
                  {metric.change}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Main Chart */}
      <div className="panel p-5 h-[380px] flex flex-col">
        <div className="flex items-center gap-2.5 mb-5 pb-3 border-b border-zinc-800/80">
          <BarChart3 className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-semibold text-zinc-100">Routing Distribution</h2>
        </div>

        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
              <CartesianGrid strokeDasharray="2 2" stroke="#27272a" vertical={false} />
              <XAxis dataKey="name" stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip
                cursor={{ fill: 'rgba(255, 255, 255, 0.03)' }}
                contentStyle={{
                  backgroundColor: '#18181b',
                  border: '1px solid #27272a',
                  borderRadius: '6px',
                  color: '#f4f4f5',
                  fontSize: '12px'
                }}
                itemStyle={{ color: '#f4f4f5' }}
              />
              <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
