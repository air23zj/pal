'use client'

import { ModuleResult } from '@/types/brief'
import { useState } from 'react'

interface ModuleCardProps {
  title: string
  module: ModuleResult
}

const statusColors = {
  ok: 'bg-green-100 text-green-800',
  degraded: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  skipped: 'bg-gray-100 text-gray-600',
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
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[module.status]}`}>
          {statusLabels[module.status]}
        </span>
      </div>
      
      {/* Summary */}
      {module.summary && (
        <p className="text-sm text-gray-600 mb-3">{module.summary}</p>
      )}
      
      {/* Counts */}
      <div className="flex gap-4 text-sm mb-4">
        {module.new_count > 0 && (
          <span className="text-blue-600 font-medium">
            {module.new_count} new
          </span>
        )}
        {module.updated_count > 0 && (
          <span className="text-orange-600 font-medium">
            {module.updated_count} updated
          </span>
        )}
        {module.new_count === 0 && module.updated_count === 0 && (
          <span className="text-gray-400">No updates</span>
        )}
      </div>
      
      {/* Items */}
      {module.items.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {expanded ? '▼ Hide' : '▶ Show'} {module.items.length} items
          </button>
          
          {expanded && (
            <div className="mt-4 space-y-3">
              {module.items.map((item) => (
                <div
                  key={item.item_ref}
                  className="p-3 bg-gray-50 rounded border border-gray-200"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-gray-900 text-sm">{item.title}</h4>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      item.novelty.label === 'NEW' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'
                    }`}>
                      {item.novelty.label}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{item.summary}</p>
                  <p className="text-xs text-blue-600 italic">{item.why_it_matters}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
