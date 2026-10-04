'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, MessageSquare, Database, Settings, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

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
    <aside className="flex h-screen w-64 flex-col bg-[#111113] border-r border-zinc-800 text-zinc-200 p-4 select-none">
      <div className="flex items-center gap-2.5 px-2 py-3 mb-6 border-b border-zinc-800/80">
        <div className="h-7 w-7 rounded-md bg-blue-600 flex items-center justify-center text-white shrink-0">
          <Activity className="h-4 w-4" />
        </div>
        <span className="text-sm font-semibold text-zinc-100 tracking-tight">
          Adaptive Chat AI
        </span>
      </div>

      <nav className="flex-1 space-y-1" aria-label="Main navigation">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-zinc-800 text-white font-medium"
                  : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/60"
              )}
            >
              <item.icon className={cn("h-4 w-4 shrink-0 transition-colors", isActive ? "text-blue-400" : "text-zinc-400")} />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>

      <div className="mt-auto px-2 py-3 border-t border-zinc-800">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-md bg-zinc-800 flex items-center justify-center border border-zinc-700/60 text-xs font-semibold text-zinc-300">
            AD
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-medium text-zinc-200 truncate">Admin User</span>
            <span className="text-[11px] text-zinc-500 truncate">admin@adaptivechat.ai</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
