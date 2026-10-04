'use client'

import React from 'react'
import { Save, Key, Database, Shield } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="space-y-6 pb-8">
      <div className="border-b border-zinc-800 pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">Settings</h1>
        <p className="text-sm text-zinc-400 mt-1">Manage API configuration, credentials, and system connectivity.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* API Credentials */}
        <div className="panel p-5">
          <div className="flex items-center gap-2.5 mb-5 pb-3 border-b border-zinc-800">
            <div className="p-1.5 bg-zinc-800 rounded text-blue-400">
              <Key className="w-4 h-4" />
            </div>
            <h2 className="text-sm font-semibold text-zinc-100">API Credentials</h2>
          </div>

          <div className="space-y-4">
            <p className="text-xs text-amber-300 bg-amber-950/40 p-3 rounded border border-amber-800/50 leading-relaxed">
              API keys are secured in the root <code>.env</code> file. The backend loads updated environment variables automatically upon reboot.
            </p>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">OpenRouter API Key</label>
              <input
                type="password"
                value="••••••••••••••••••••••••"
                disabled
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-500 cursor-not-allowed focus:outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Groq API Key</label>
              <input
                type="password"
                value="••••••••••••••••••••••••"
                disabled
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-500 cursor-not-allowed focus:outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Google Gemini API Key</label>
              <input
                type="password"
                value="••••••••••••••••••••••••"
                disabled
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-500 cursor-not-allowed focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* System Services & Security */}
        <div className="space-y-6">
          <div className="panel p-5">
            <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-zinc-800">
              <div className="p-1.5 bg-zinc-800 rounded text-emerald-400">
                <Database className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-semibold text-zinc-100">Database and Cache Status</h2>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-zinc-800/60 text-xs">
                <span className="text-zinc-400">Database Engine (PostgreSQL / SQLite)</span>
                <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <span className="w-1.5 h-1.5 rounded-sm bg-emerald-400"></span>
                  Active
                </span>
              </div>
              <div className="flex justify-between items-center py-2 text-xs">
                <span className="text-zinc-400">Redis Cache & Memory</span>
                <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <span className="w-1.5 h-1.5 rounded-sm bg-emerald-400"></span>
                  Connected
                </span>
              </div>
            </div>
          </div>

          <div className="panel p-5">
            <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-zinc-800">
              <div className="p-1.5 bg-zinc-800 rounded text-blue-400">
                <Shield className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-semibold text-zinc-100">Security and Routing Limits</h2>
            </div>

            <p className="text-xs text-zinc-400 mb-4 leading-relaxed">
              Input queries are validated against token budget ceilings. Cross-origin requests are constrained to configured CORS origins.
            </p>

            <button className="flex items-center justify-center gap-2 w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium transition-colors">
              <Save className="w-3.5 h-3.5" />
              Save Preferences
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
