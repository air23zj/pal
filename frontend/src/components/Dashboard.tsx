'use client'

import { BriefBundle } from '@/types/brief'
import { useState, useCallback, useEffect } from 'react'
import { getLatestBrief, triggerBriefRun, getRunStatus, getUserSettings, saveUserSettings } from '@/lib/api'
import Header from './Header'
import ModuleCard from './ModuleCard'
import SettingsModal, { UserSettings } from './SettingsModal'

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
  const handleSearch = () => {
    window.location.href = '/search'
  }
  const [currentBrief, setCurrentBrief] = useState(brief)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

  // Default user settings - will be loaded from backend
  const [userSettings, setUserSettings] = useState<UserSettings>({
    topics: ['AI', 'technology', 'startups'],
    vip_people: [],
    projects: [],
    enabled_modules: ['gmail', 'calendar', 'tasks', 'news', 'research', 'flights', 'dining', 'travel', 'local', 'shopping'],
  })

  // Load user settings from backend on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const settings = await getUserSettings()
        setUserSettings(settings)
      } catch (error) {
        console.warn('Failed to load user settings, using defaults:', error)
        // Keep default settings if loading fails
      }
    }
    loadSettings()
  }, [])

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true)
    setError(null)

    try {
      // Trigger a new brief run (real run)
      const { run_id } = await triggerBriefRun(true)

      // Poll for completion (max 60 seconds)
      const startTime = Date.now()
      let status = 'queued'

      while ((status === 'queued' || status === 'running') && (Date.now() - startTime < 60000)) {
        // Wait 2 seconds between polls
        await new Promise(resolve => setTimeout(resolve, 2000))

        const runInfo = await getRunStatus(run_id)
        status = runInfo.status

        if (status === 'error') {
          throw new Error('Brief generation failed on server')
        }
      }

      const newBrief = await getLatestBrief()
      setCurrentBrief(newBrief)
    } catch (err) {
      console.error('Failed to refresh brief:', err)
      setError('Failed to refresh brief. Please try again.')
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  const handleOpenSettings = useCallback(() => {
    setIsSettingsOpen(true)
  }, [])

  const handleSaveSettings = useCallback(async (settings: UserSettings) => {
    try {
      await saveUserSettings('u_dev', settings)
      setUserSettings(settings)
      console.log('Settings saved successfully')
    } catch (error) {
      console.error('Failed to save settings:', error)
      // Still update local state even if save fails
      setUserSettings(settings)
    }
  }, [])

  // Get module entries, filtering out any with status 'skipped' and no items
  const moduleEntries = Object.entries(currentBrief.modules).filter(
    ([_, module]) => module.status !== 'skipped' || module.items.length > 0
  )

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <Header
        brief={currentBrief}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
        onOpenSettings={handleOpenSettings}
        onSearch={handleSearch}
      />

      {/* Error message */}
      {error && (
        <div className="mb-8 p-5 bg-error-50 border border-error-200 text-error-700 rounded-xl animate-fade-in">
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            {error}
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {isRefreshing && (
        <div className="mb-8 p-5 bg-primary-50 border border-primary-200 text-primary-700 rounded-xl animate-fade-in">
          <div className="flex items-center">
            <svg className="animate-spin h-5 w-5 mr-3 flex-shrink-0" viewBox="0 0 24 24">
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
            <span className="font-medium">Refreshing your brief...</span>
          </div>
        </div>
      )}

      {/* Top Highlights */}
      {currentBrief.top_highlights.length > 0 && (
        <section className="mb-12 animate-fade-in">
          <div className="flex items-center mb-6">
            <div className="w-1 h-8 bg-primary-500 rounded-full mr-4"></div>
            <h2 className="text-2xl font-semibold text-neutral-900">Top Highlights</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {currentBrief.top_highlights.map((item, index) => (
              <div
                key={item.item_ref}
                className="card group hover:scale-[1.02] transition-transform duration-200 animate-slide-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="card-body">
                  <div className="w-2 h-12 bg-gradient-to-b from-primary-500 to-primary-600 rounded-full mb-4 group-hover:from-primary-600 group-hover:to-primary-700 transition-colors"></div>
                  <h3 className="text-lg font-semibold text-neutral-900 mb-3 leading-tight">{item.title}</h3>
                  <p className="text-neutral-700 mb-4 leading-relaxed">{item.summary}</p>
                  <div className="flex items-start">
                    <svg className="w-4 h-4 text-primary-500 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm text-primary-700 font-medium leading-relaxed">{item.why_it_matters}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Modules Grid - dynamically rendered based on available modules */}
      <section className="animate-fade-in">
        <div className="flex items-center mb-8">
          <div className="w-1 h-8 bg-primary-500 rounded-full mr-4"></div>
          <h2 className="text-2xl font-semibold text-neutral-900">Your Brief</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
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
      </section>

      {/* Show message if no modules */}
      {moduleEntries.length === 0 && (
        <div className="text-center py-16 animate-fade-in">
          <div className="w-16 h-16 mx-auto mb-6 bg-neutral-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-neutral-900 mb-2">No modules available yet</h3>
          <p className="text-neutral-700 max-w-md mx-auto leading-relaxed">
            Configure your data sources in settings to start receiving personalized briefings.
          </p>
        </div>
      )}

      {/* Metadata */}
      <div className="mt-12 p-6 surface-secondary rounded-xl animate-fade-in">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div className="flex items-center text-sm text-neutral-700">
            <svg className="w-4 h-4 mr-2 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">
              Generated: {new Date(currentBrief.generated_at_utc).toLocaleString()}
            </span>
          </div>
          <div className="flex items-center text-sm text-neutral-700">
            <svg className="w-4 h-4 mr-2 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="font-medium">
              Latency: {currentBrief.run_metadata?.latency_ms ?? 'N/A'}ms
            </span>
          </div>
        </div>
        {currentBrief.run_metadata?.warnings && currentBrief.run_metadata.warnings.length > 0 && (
          <div className="mt-4 p-3 bg-warning-50 border border-warning-200 rounded-lg">
            <div className="flex items-start">
              <svg className="w-4 h-4 text-warning-500 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-warning-800 mb-1">Warnings</p>
                <p className="text-sm text-warning-700">{currentBrief.run_metadata.warnings.join(', ')}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSave={handleSaveSettings}
        currentSettings={userSettings}
      />
    </div>
  )
}
