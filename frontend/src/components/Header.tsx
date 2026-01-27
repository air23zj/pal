'use client'

import { BriefBundle } from '@/types/brief'
import { format } from 'date-fns'

interface HeaderProps {
  brief: BriefBundle
  onRefresh: () => void
  isRefreshing?: boolean
  onOpenSettings?: () => void
  onSearch?: () => void
}

export default function Header({ brief, onRefresh, isRefreshing = false, onOpenSettings, onSearch }: HeaderProps) {
  const briefDate = new Date(brief.generated_at_utc)

  return (
    <header className="mb-12 animate-fade-in">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-4xl font-bold text-neutral-900 tracking-tight">
            Good morning
          </h1>
          <p className="text-neutral-600 mt-3 text-lg">
            Brief since {format(new Date(brief.since_timestamp_utc), 'MMMM d, yyyy h:mm a')}
          </p>
        </div>

        <div className="flex gap-4">
          <button
            onClick={onSearch}
            className="btn-secondary flex items-center gap-2 font-medium"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Search
          </button>
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className={`btn-primary flex items-center gap-2 font-medium ${
              isRefreshing ? 'opacity-75 cursor-not-allowed' : ''
            }`}
          >
            {isRefreshing ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Refreshing...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </>
            )}
          </button>
          <button
            onClick={onOpenSettings}
            className="btn-ghost font-medium"
          >
            Settings
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="flex items-center gap-6 text-sm text-neutral-500">
        <div className="flex items-center gap-1.5">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-medium">{format(briefDate, 'h:mm a')}</span>
        </div>
        <div className="w-px h-4 bg-neutral-300"></div>
        <div className="flex items-center gap-1.5">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="font-medium">{brief.timezone}</span>
        </div>
      </div>
    </header>
  )
}
