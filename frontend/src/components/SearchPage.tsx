'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { performSearch, summarizeYouTube, SearchResult, YouTubeResult } from '@/lib/api'

export default function SearchPage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [youtubeUrl, setYoutubeUrl] = useState('https://www.youtube.com/watch?v=y2NeAef6d30&t=1928s')
  const [isSearching, setIsSearching] = useState(false)
  const [isSummarizing, setIsSummarizing] = useState(false)
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null)
  const [youtubeResult, setYoutubeResult] = useState<YouTubeResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'search' | 'youtube'>('search')

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query')
      return
    }

    setIsSearching(true)
    setError(null)
    setSearchResult(null)

    try {
      const result = await performSearch(searchQuery, 'serper')
      setSearchResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setIsSearching(false)
    }
  }

  const handleYouTubeSummarize = async () => {
    if (!youtubeUrl.trim()) {
      setError('Please enter a YouTube URL')
      return
    }

    setIsSummarizing(true)
    setError(null)
    setYoutubeResult(null)

    try {
      const result = await summarizeYouTube(youtubeUrl)
      setYoutubeResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'YouTube summarization failed')
    } finally {
      setIsSummarizing(false)
    }
  }

  const handleRelatedQuestionClick = (question: string) => {
    setSearchQuery(question)
    handleSearch()
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="flex items-center justify-between mb-10 animate-fade-in">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900 tracking-tight">AI-Powered Search</h1>
            <p className="text-neutral-700 mt-2">Discover and analyze information with AI assistance</p>
          </div>
          <button
            onClick={() => router.push('/')}
            className="btn-ghost flex items-center gap-2"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Dashboard
          </button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-10 bg-neutral-100 p-1.5 rounded-xl shadow-apple-sm">
          <button
            onClick={() => setActiveTab('search')}
            className={`flex-1 py-3 px-6 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === 'search'
                ? 'bg-white text-neutral-900 shadow-apple-md transform scale-[1.02]'
                : 'text-neutral-700 hover:text-neutral-800 hover:bg-white/50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Web Search
            </div>
          </button>
          <button
            onClick={() => setActiveTab('youtube')}
            className={`flex-1 py-3 px-6 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === 'youtube'
                ? 'bg-white text-neutral-900 shadow-apple-md transform scale-[1.02]'
                : 'text-neutral-700 hover:text-neutral-800 hover:bg-white/50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              YouTube Summary
            </div>
          </button>
        </div>

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <div className="flex gap-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Ask me anything..."
                className="input-primary text-base"
              />
              <button
                onClick={handleSearch}
                disabled={isSearching}
                className="btn-primary px-8 py-3 text-base font-medium flex items-center gap-2"
              >
                {isSearching ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Searching...
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    Search
                  </>
                )}
              </button>
            </div>

            {/* Search Results */}
            {searchResult && (
              <div className="space-y-8">
                {/* Answer */}
                <div className="bg-white p-6 rounded-lg shadow-sm">
                  <div className="prose max-w-none">
                    {searchResult.answer.split('\n').map((paragraph, index) => (
                      <p key={index} className="mb-4 text-gray-800 leading-relaxed">{paragraph}</p>
                    ))}
                  </div>
                </div>

                {/* Sources */}
                <div>
                  <h3 className="text-xl font-semibold mb-6 text-gray-900">Sources</h3>
                  <div className="space-y-4">
                    {searchResult.sources.map((source, index) => (
                      <div key={index} id={`source-${index + 1}`} className="bg-white p-4 rounded-lg shadow-sm">
                        <div className="flex justify-between items-start mb-3">
                          <h4 className="font-semibold text-blue-700 text-base leading-tight">{source.title}</h4>
                          <span className="text-sm font-medium text-gray-600 bg-gray-100 px-2 py-1 rounded-full">[{index + 1}]</span>
                        </div>
                        <p className="text-sm text-gray-800 mb-3 leading-relaxed">{source.snippet}</p>
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-700 hover:underline transition-colors"
                        >
                          Read more →
                          <svg className="ml-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Related Questions */}
                {searchResult.related_questions.length > 0 && (
                  <div>
                    <h3 className="text-xl font-semibold mb-6 text-gray-900">Related Questions</h3>
                    <div className="space-y-2">
                      {searchResult.related_questions.map((question, index) => (
                        <button
                          key={index}
                          onClick={() => handleRelatedQuestionClick(question)}
                          className="w-full text-left p-4 rounded-lg hover:bg-blue-50 text-blue-700 hover:text-blue-800 transition-colors border border-gray-200 hover:border-blue-300 bg-white hover:bg-blue-25"
                        >
                          <span className="font-medium">{question}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* YouTube Tab */}
        {activeTab === 'youtube' && (
          <div className="space-y-6">
            <div className="flex gap-4">
              <input
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleYouTubeSummarize()}
                placeholder="https://www.youtube.com/watch?v=VIDEO_ID"
                className="input-primary text-base"
              />
              <button
                onClick={handleYouTubeSummarize}
                disabled={isSummarizing}
                className="btn-primary px-8 py-3 text-base font-medium flex items-center gap-2"
              >
                {isSummarizing ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Summarizing...
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Summarize
                  </>
                )}
              </button>
            </div>

            {/* YouTube Summary */}
            {youtubeResult && (
              <div className="space-y-6">
                {/* Video Metadata */}
                {youtubeResult.metadata && (
                  <div className="card">
                    <div className="card-body">
                      <div className="flex items-start space-x-4">
                        {youtubeResult.metadata.thumbnail_url && (
                          <img
                            src={youtubeResult.metadata.thumbnail_url}
                            alt="Video thumbnail"
                            className="w-24 h-18 object-cover rounded-lg flex-shrink-0"
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-neutral-900 mb-1 leading-tight">
                            {youtubeResult.metadata.title || 'YouTube Video'}
                          </h3>
                          {youtubeResult.metadata.channel_title && (
                            <p className="text-sm text-neutral-600 mb-2">
                              {youtubeResult.metadata.channel_title}
                            </p>
                          )}
                          <div className="flex items-center space-x-4 text-xs text-neutral-600">
                            {youtubeResult.metadata.view_count && (
                              <span>{parseInt(youtubeResult.metadata.view_count).toLocaleString()} views</span>
                            )}
                            {youtubeResult.metadata.published_at && (
                              <span>{new Date(youtubeResult.metadata.published_at).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Summary */}
                <div className="card">
                  <div className="card-body">
                    <h3 className="text-xl font-semibold mb-4 text-neutral-900">Video Summary</h3>
                    <div className="prose max-w-none">
                      {youtubeResult.summary.split('\n').map((line, index) => (
                        <div key={index} className="mb-3">
                          {line.startsWith('#') ? (
                            <h4 className="text-lg font-semibold mt-6 mb-3 text-neutral-900 border-b border-neutral-200 pb-2">{line.replace('#', '').trim()}</h4>
                          ) : line.startsWith('- ') ? (
                            <div className="flex items-start ml-4">
                              <span className="text-primary-500 mr-2 mt-1.5">•</span>
                              <span className="text-neutral-800 leading-relaxed">{line.substring(2)}</span>
                            </div>
                          ) : line.trim() ? (
                            <p className="text-neutral-800 leading-relaxed">{line}</p>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Loading Indicator */}
        {(isSearching || isSummarizing) && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}