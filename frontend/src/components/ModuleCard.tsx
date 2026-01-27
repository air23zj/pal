'use client'

import { ModuleResult } from '@/types/brief'
import { useState } from 'react'

interface ModuleCardProps {
  title: string
  module: ModuleResult
}

const statusColors = {
  ok: 'bg-success-100 text-success-700 border-success-200',
  degraded: 'bg-warning-100 text-warning-700 border-warning-200',
  error: 'bg-error-100 text-error-700 border-error-200',
  skipped: 'bg-neutral-100 text-neutral-700 border-neutral-200',
}

const statusLabels = {
  ok: 'Active',
  degraded: 'Degraded',
  error: 'Error',
  skipped: 'Skipped',
}

export default function ModuleCard({ title, module }: ModuleCardProps) {
  const [expanded, setExpanded] = useState(false)
  
  return (
    <div className="card group">
      {/* Header */}
      <div className="card-header">
        <div className="flex justify-between items-start">
          <h3 className="text-lg font-semibold text-neutral-900 group-hover:text-primary-900 transition-colors">{title}</h3>
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${statusColors[module.status]} group-hover:scale-105 transition-transform`}>
            {statusLabels[module.status]}
          </span>
        </div>
      </div>

      {/* Summary */}
      {module.summary && (
        <p className="text-sm text-neutral-700 mb-4 leading-relaxed">{module.summary}</p>
      )}

      {/* Counts */}
      <div className="flex gap-6 text-sm mb-6">
        {module.new_count > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
            <span className="text-primary-700 font-semibold">
              {module.new_count} new
            </span>
          </div>
        )}
        {module.updated_count > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-warning-500 rounded-full"></div>
            <span className="text-warning-700 font-semibold">
              {module.updated_count} updated
            </span>
          </div>
        )}
        {module.new_count === 0 && module.updated_count === 0 && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-neutral-300 rounded-full"></div>
            <span className="text-neutral-500 font-medium">No updates</span>
          </div>
        )}
      </div>
      
      {/* Items */}
      {module.items.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors group"
          >
            <svg
              className={`w-4 h-4 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {expanded ? 'Hide' : 'Show'} {module.items.length} items
          </button>

          {expanded && (
            <div className="mt-6 space-y-4 animate-slide-up">
              {module.items.map((item, index) => (
                <div
                  key={item.item_ref}
                  className="p-4 bg-neutral-50 rounded-lg border border-neutral-200 hover:border-neutral-300 transition-colors"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="font-medium text-neutral-900 text-sm leading-tight pr-3">{item.title}</h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium flex-shrink-0 ${
                      item.novelty.label === 'NEW'
                        ? 'bg-primary-100 text-primary-700 border border-primary-200'
                        : 'bg-warning-100 text-warning-700 border border-warning-200'
                    }`}>
                      {item.novelty.label}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-700 mb-3 leading-relaxed">{item.summary}</p>
                  <div className="flex items-start">
                    <svg className="w-3 h-3 text-primary-500 mr-2 mt-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm text-primary-700 font-medium leading-relaxed">{item.why_it_matters}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
