'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity, DollarSign, Zap, Database, TrendingUp, BarChart3, Loader2 } from 'lucide-react'
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts'

export default function AnalyticsDashboard() {
  const [stats, setStats] = useState<any[]>([]);
  const [usageData, setUsageData] = useState<any[]>([]);
  const [providerData, setProviderData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const [summaryRes, timeSeriesRes, providerRes] = await Promise.all([
          fetch(`${apiUrl}/api/v1/analytics/summary`),
          fetch(`${apiUrl}/api/v1/analytics/time-series`),
          fetch(`${apiUrl}/api/v1/analytics/cost-by-provider`)
        ]);
        
        const summaryData = await summaryRes.json();
        const timeSeriesData = await timeSeriesRes.json();
        const providerData = await providerRes.json();
        
        setStats([
          { name: 'Total Tokens', value: summaryData.total_tokens.toLocaleString(), change: '', icon: Database, color: 'text-blue-400' },
          { name: 'Estimated Cost', value: `$${summaryData.total_cost_usd.toFixed(4)}`, change: '', icon: DollarSign, color: 'text-emerald-400' },
          { name: 'Cache Hit Rate', value: `${summaryData.cache_hit_rate.toFixed(1)}%`, change: '', icon: Zap, color: 'text-amber-400' },
          { name: 'Avg Latency', value: `${summaryData.avg_latency_ms.toFixed(0)}ms`, change: '', icon: Activity, color: 'text-primary' },
        ]);
        
        setUsageData(timeSeriesData);
        setProviderData(providerData);

      } catch (error) {
        console.error("Failed to fetch analytics:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalytics();
  }, []);

  const COLORS = ['#00f0ff', '#8b5cf6', '#3b82f6', '#ec4899', '#10b981'];

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
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
            Analytics & Cost
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-white/60"
          >
            Monitor real-time LLM usage, routing performance, and token expenditure.
          </motion.p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <motion.div
            key={stat.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + (idx * 0.1) }}
            className="glass-panel p-6 rounded-2xl relative overflow-hidden group"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 bg-white/5 rounded-xl ${stat.color} group-hover:scale-110 transition-transform`}>
                <stat.icon className="h-6 w-6" />
              </div>
              {stat.change && (
                <span className="text-xs font-semibold text-emerald-400">
                  {stat.change}
                </span>
              )}
            </div>
            <div>
              <h3 className="text-3xl font-bold text-white mb-1">{stat.value}</h3>
              <p className="text-white/50 text-sm font-medium">{stat.name}</p>
            </div>
            <div className="absolute -bottom-6 -right-6 opacity-[0.03] group-hover:opacity-[0.05] transition-opacity">
              <stat.icon className="h-32 w-32" />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Charts Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Token Usage Chart */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
          className="glass-panel p-6 rounded-2xl lg:col-span-2"
        >
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-white">Token Usage Over Time</h2>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={usageData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#fc80ff" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#fc80ff" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="time" stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area type="monotone" dataKey="tokens" stroke="#fc80ff" strokeWidth={3} fillOpacity={1} fill="url(#colorTokens)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Cost by Provider Chart */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="glass-panel p-6 rounded-2xl"
        >
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="h-5 w-5 text-secondary" />
            <h2 className="text-lg font-semibold text-white">Cost by Provider</h2>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={providerData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="provider" stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                />
                <Bar dataKey="cost" radius={[4, 4, 0, 0]}>
                  {providerData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

      </div>
    </div>
  )
}
