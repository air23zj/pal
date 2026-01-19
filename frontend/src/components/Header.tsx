'use client'

import { BriefBundle } from '@/types/brief'
import { format } from 'date-fns'

interface HeaderProps {
  brief: BriefBundle
  onRefresh: () => void
  isRefreshing?: boolean
}

export default function Header({ brief, onRefresh, isRefreshing = false }: HeaderProps) {
  const briefDate = new Date(brief.generated_at_utc)

  return (
    <header className="mb-8">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h1 className="text-4xl font-bold text-gray-900">
            Good morning
          </h1>
          <p className="text-gray-600 mt-2">
            Brief since {format(new Date(brief.since_timestamp_utc), 'MMMM d, yyyy h:mm a')}
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              isRefreshing
                ? 'bg-gray-400 text-white cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
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
              'Refresh'
            )}
          </button>
          <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
            Settings
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="flex gap-4 text-sm text-gray-600">
        <span>{format(briefDate, 'h:mm a')}</span>
        <span>|</span>
        <span>{brief.timezone}</span>
      </div>
    </header>
  )
}
