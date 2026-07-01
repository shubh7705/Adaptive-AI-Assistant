'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, MessageSquare, Database, Settings, Activity } from 'lucide-react'
import { motion } from 'framer-motion'
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const navItems = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Chat Stream', href: '/chat', icon: MessageSquare },
  { name: 'Model Registry', href: '/models', icon: Database },
  { name: 'Analytics', href: '/analytics', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-screen w-64 flex-col glass-panel border-r border-white/5 border-l-0 border-y-0 text-white p-4">
      <div className="flex items-center gap-3 px-2 py-4 mb-8">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-[0_0_15px_rgba(252,128,255,0.5)]">
          <Activity className="h-5 w-5 text-white" />
        </div>
        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
          ModelRouter AI
        </span>
      </div>

      <nav className="flex-1 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link key={item.name} href={item.href}>
              <motion.div
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all relative overflow-hidden",
                  isActive
                    ? "text-white"
                    : "text-white/60 hover:text-white hover:bg-white/5"
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-pill"
                    className="absolute inset-0 bg-primary/10 rounded-lg border border-primary/20"
                    initial={false}
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <item.icon className={cn("h-5 w-5 z-10 transition-colors", isActive ? "text-primary" : "")} />
                <span className="z-10">{item.name}</span>
              </motion.div>
            </Link>
          )
        })}
      </nav>

      <div className="mt-auto px-2 py-4 border-t border-white/10">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-secondary flex items-center justify-center border border-white/10">
            <span className="text-sm font-semibold">AD</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-white/90">Admin User</span>
            <span className="text-xs text-white/50">admin@modelrouter.ai</span>
          </div>
        </div>
      </div>
    </div>
  )
}
