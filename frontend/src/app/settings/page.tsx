'use client';

import React from 'react';
import { Save, Key, Database, Shield } from 'lucide-react';
import { motion } from 'framer-motion';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Settings</h1>
        <p className="text-gray-400">Manage your AI API keys and system configuration.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-indigo-500/20 rounded-lg">
              <Key className="w-5 h-5 text-indigo-400" />
            </div>
            <h2 className="text-xl font-semibold text-white">API Keys</h2>
          </div>
          
          <div className="space-y-4">
            <p className="text-sm text-yellow-400/90 bg-yellow-400/10 p-3 rounded-lg border border-yellow-400/20 mb-4">
              To keep your keys secure, please configure them directly in the <code>.env</code> file in the root of your project. The backend will automatically pick them up on restart.
            </p>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">OpenRouter API Key</label>
              <input 
                type="password" 
                value="••••••••••••••••••••••••"
                disabled
                className="w-full px-4 py-2 bg-black/40 border border-white/10 rounded-lg text-gray-500 cursor-not-allowed focus:outline-none"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Groq API Key</label>
              <input 
                type="password" 
                value="••••••••••••••••••••••••"
                disabled
                className="w-full px-4 py-2 bg-black/40 border border-white/10 rounded-lg text-gray-500 cursor-not-allowed focus:outline-none"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Google Gemini API Key</label>
              <input 
                type="password" 
                value="••••••••••••••••••••••••"
                disabled
                className="w-full px-4 py-2 bg-black/40 border border-white/10 rounded-lg text-gray-500 cursor-not-allowed focus:outline-none"
              />
            </div>
          </div>
        </motion.div>

        <div className="space-y-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <Database className="w-5 h-5 text-emerald-400" />
              </div>
              <h2 className="text-xl font-semibold text-white">Database Status</h2>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-gray-400">PostgreSQL Analytics</span>
                <span className="flex items-center gap-2 text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  Connected
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-gray-400">Redis Semantic Cache</span>
                <span className="flex items-center gap-2 text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  Connected
                </span>
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-rose-500/20 rounded-lg">
                <Shield className="w-5 h-5 text-rose-400" />
              </div>
              <h2 className="text-xl font-semibold text-white">Security</h2>
            </div>
            
            <p className="text-sm text-gray-400 mb-4">
              All API requests between the frontend and backend are secured. The router enforces strict token limits to prevent cost overruns.
            </p>
            
            <button className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-white/10 hover:bg-white/15 text-white rounded-lg transition-colors">
              <Save className="w-4 h-4" />
              Save Preferences
            </button>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
