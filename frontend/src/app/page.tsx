'use client'

import { motion } from 'framer-motion'
import { Activity, Zap, Server, DollarSign, BrainCircuit, LineChart } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// Mock Data
const metrics = [
  { title: "Total Requests", value: "24,593", change: "+12.5%", icon: Activity, color: "text-blue-400" },
  { title: "Cache Hit Rate", value: "42.8%", change: "+5.2%", icon: Zap, color: "text-yellow-400" },
  { title: "Avg Latency", value: "342ms", change: "-18ms", icon: Server, color: "text-emerald-400" },
  { title: "Total Cost", value: "$142.50", change: "-$12.30", icon: DollarSign, color: "text-red-400" },
]

const chartData = [
  { time: '00:00', deepseek: 40, gemma: 24, gpt4: 10 },
  { time: '04:00', deepseek: 30, gemma: 13, gpt4: 5 },
  { time: '08:00', deepseek: 120, gemma: 58, gpt4: 45 },
  { time: '12:00', deepseek: 250, gemma: 110, gpt4: 85 },
  { time: '16:00', deepseek: 210, gemma: 90, gpt4: 70 },
  { time: '20:00', deepseek: 150, gemma: 65, gpt4: 40 },
  { time: '24:00', deepseek: 60, gemma: 30, gpt4: 15 },
]

export default function Dashboard() {
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
            {/* Background Glow */}
            <div className="absolute -right-10 -top-10 w-32 h-32 bg-white/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-colors duration-500" />
            
            <div className="flex items-center justify-between mb-4 relative z-10">
              <span className="text-sm font-medium text-white/60">{metric.title}</span>
              <metric.icon className={`h-5 w-5 ${metric.color}`} />
            </div>
            <div className="flex items-baseline gap-2 relative z-10">
              <h2 className="text-3xl font-bold text-white">{metric.value}</h2>
              <span className={`text-xs font-medium ${metric.change.startsWith('+') && metric.title !== "Total Cost" ? 'text-emerald-400' : 'text-emerald-400'}`}>
                {metric.change}
              </span>
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
            <LineChart className="h-5 w-5 text-primary" />
          </div>
          <h3 className="text-lg font-semibold text-white">Routing Distribution Over Time</h3>
        </div>
        
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorDeepseek" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorGemma" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="rgba(255,255,255,0.5)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: 'white' }}
                itemStyle={{ color: 'white' }}
              />
              <Area type="monotone" dataKey="deepseek" name="DeepSeek V3" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorDeepseek)" />
              <Area type="monotone" dataKey="gemma" name="Gemma 3 12B" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorGemma)" />
              <Area type="monotone" dataKey="gpt4" name="GPT-4o" stroke="#ec4899" strokeWidth={2} fillOpacity={1} fill="transparent" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>
    </div>
  )
}
