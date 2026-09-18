'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity, Zap, Server, BrainCircuit, BarChart3, Loader2, type LucideIcon } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Array<{ title: string; value: string; change: string; icon: LucideIcon; color: string }>>([]);
  const [chartData, setChartData] = useState<Array<{ name: string; count: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const [summaryRes, distRes] = await Promise.all([
          fetch(`${apiUrl}/api/v1/analytics/summary`, { headers }),
          fetch(`${apiUrl}/api/v1/analytics/routing-distribution`, { headers })
        ]);
        
        if (!summaryRes.ok || !distRes.ok) throw new Error('Analytics request failed')
        const summaryData: { total_requests?: number; cache_hit_rate?: number; avg_latency_ms?: number; total_tokens?: number } = await summaryRes.json();
        const distData: { distribution: Record<string, number> } = await distRes.json();
        
        // Map backend summary to frontend metric cards
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
            color: "text-yellow-400" 
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
            color: "text-purple-400" 
          },
        ]);

        // Map backend distribution to Recharts BarChart format
        const formattedChartData = Object.entries(distData.distribution).map(([name, count]) => ({
          name: name.split('/').pop() || name, // simplify long model names
          count: count
        }));
        
        setChartData(formattedChartData);
      } catch (error) {
        console.error("Failed to fetch analytics:", error);
        setError("Failed to load analytics data. Please check your connection.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalytics();
  }, []);

  const COLORS = ['#8b5cf6', '#3b82f6', '#ec4899', '#10b981', '#f59e0b'];

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-2">{error}</p>
          <button onClick={() => window.location.reload()} className="text-primary hover:underline text-sm">
            Retry
          </button>
        </div>
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
            System Overview
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-white/60"
          >
            Monitor real-time AI routing analytics and model performance.
          </motion.p>
        </div>
        <motion.div 
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
        >
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-sm font-medium">System Optimal</span>
        </motion.div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-panel p-6 rounded-2xl relative overflow-hidden group"
          >
            <div className="absolute -right-10 -top-10 w-32 h-32 bg-white/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-colors duration-500" />
            
            <div className="flex items-center justify-between mb-4 relative z-10">
              <span className="text-sm font-medium text-white/60">{metric.title}</span>
              <metric.icon className={`h-5 w-5 ${metric.color}`} />
            </div>
            <div className="flex items-baseline gap-2 relative z-10">
              <h2 className="text-3xl font-bold text-white">{metric.value}</h2>
              {metric.change && (
                <span className="text-xs font-medium text-emerald-400">
                  {metric.change}
                </span>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Main Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-panel p-6 rounded-2xl h-[400px] flex flex-col"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-primary/20 border border-primary/30">
            <BarChart3 className="h-5 w-5 text-primary" />
          </div>
          <h3 className="text-lg font-semibold text-white">Routing Distribution</h3>
        </div>
        
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="rgba(255,255,255,0.5)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: 'white' }}
                itemStyle={{ color: 'white' }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>
    </div>
  )
}
