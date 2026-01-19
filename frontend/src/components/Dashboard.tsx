'use client'

import { BriefBundle } from '@/types/brief'
import { useState, useCallback } from 'react'
import { getLatestBrief, triggerBriefRun } from '@/lib/api'
import Header from './Header'
import ModuleCard from './ModuleCard'

interface DashboardProps {
  brief: BriefBundle
}

// Module display configuration with icons
const MODULE_CONFIG: Record<string, { icon: string; title: string }> = {
  gmail: { icon: '📧', title: 'Inbox' },
  calendar: { icon: '📅', title: 'Calendar' },
  tasks: { icon: '✅', title: 'Tasks' },
  news: { icon: '📰', title: 'News' },
  twitter: { icon: '🐦', title: 'Twitter/X' },
  x: { icon: '🐦', title: 'Twitter/X' },
  linkedin: { icon: '💼', title: 'LinkedIn' },
  research: { icon: '🔬', title: 'Research' },
  arxiv: { icon: '📄', title: 'arXiv' },
  podcasts: { icon: '🎙️', title: 'Podcasts' },
  weather: { icon: '☀️', title: 'Weather' },
  commute: { icon: '🚗', title: 'Commute' },
}

function getModuleDisplay(key: string): { icon: string; title: string } {
  return MODULE_CONFIG[key] || { icon: '📦', title: key.charAt(0).toUpperCase() + key.slice(1) }
}

export default function Dashboard({ brief }: DashboardProps) {
  const [currentBrief, setCurrentBrief] = useState(brief)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true)
    setError(null)

    try {
      // Trigger a new brief run
      await triggerBriefRun()

      // Wait a moment for processing, then fetch latest
      await new Promise(resolve => setTimeout(resolve, 1000))

      const newBrief = await getLatestBrief()
      setCurrentBrief(newBrief)
    } catch (err) {
      console.error('Failed to refresh brief:', err)
      setError('Failed to refresh brief. Please try again.')
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  // Get module entries, filtering out any with status 'skipped' and no items
  const moduleEntries = Object.entries(currentBrief.modules).filter(
    ([_, module]) => module.status !== 'skipped' || module.items.length > 0
  )

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Header
        brief={currentBrief}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading overlay */}
      {isRefreshing && (
        <div className="mb-6 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded-lg flex items-center">
          <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Refreshing your brief...
        </div>
      )}

      {/* Top Highlights */}
      {currentBrief.top_highlights.length > 0 && (
        <section className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Top Highlights</h2>
          <div className="space-y-4">
            {currentBrief.top_highlights.map((item) => (
              <div
                key={item.item_ref}
                className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500"
              >
                <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                <p className="text-gray-700 mb-2">{item.summary}</p>
                <p className="text-sm text-blue-600 italic">{item.why_it_matters}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Modules Grid - dynamically rendered based on available modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {moduleEntries.map(([key, module]) => {
          const display = getModuleDisplay(key)
          return (
            <ModuleCard
              key={key}
              title={`${display.icon} ${display.title}`}
              module={module}
            />
          )
        })}
      </div>

      {/* Show message if no modules */}
      {moduleEntries.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg">No modules available yet.</p>
          <p className="text-sm mt-2">Configure your data sources to get started.</p>
        </div>
      )}

      {/* Metadata */}
      <div className="mt-8 p-4 bg-gray-100 rounded-lg text-sm text-gray-600">
        <div className="flex justify-between items-center">
          <span>
            Generated: {new Date(currentBrief.generated_at_utc).toLocaleString()}
          </span>
          <span>
            Latency: {currentBrief.run_metadata?.latency_ms ?? 'N/A'}ms
          </span>
        </div>
        {currentBrief.run_metadata?.warnings && currentBrief.run_metadata.warnings.length > 0 && (
          <div className="mt-2 text-yellow-600">
            {currentBrief.run_metadata.warnings.join(', ')}
          </div>
        )}
      </div>
    </div>
  )
}
