/**
 * API client for Morning Brief backend
 */
import { BriefBundle } from '@/types/brief'
import { UserSettings } from '@/components/SettingsModal'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function getLatestBrief(): Promise<BriefBundle> {
  const res = await fetch(`${API_BASE}/api/brief/latest`, {
    cache: 'no-store',
  })

  if (!res.ok) {
    throw new Error('Failed to fetch latest brief')
  }

  return res.json()
}

export async function triggerBriefRun(runOrchestrator: boolean = true): Promise<{ run_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/api/brief/run?run_orchestrator=${runOrchestrator}`, {
    method: 'POST',
  })

  if (!res.ok) {
    throw new Error('Failed to trigger brief run')
  }

  return res.json()
}

export async function getRunStatus(run_id: string): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/brief/run/${run_id}`)

  if (!res.ok) {
    throw new Error('Failed to fetch run status')
  }

  return res.json()
}

export async function recordFeedback(
  item_ref: string,
  event_type: string,
  payload?: Record<string, any>
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      item_ref,
      event_type,
      payload,
    }),
  })

  if (!res.ok) {
    throw new Error('Failed to record feedback')
  }
}

export async function markItemSeen(item_ref: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/item/mark_seen`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      item_ref,
    }),
  })

  if (!res.ok) {
    throw new Error('Failed to mark item as seen')
  }
}

export async function getUserSettings(userId: string = 'u_dev'): Promise<UserSettings> {
  const res = await fetch(`${API_BASE}/api/settings/${userId}`)

  if (!res.ok) {
    throw new Error('Failed to fetch user settings')
  }

  return res.json()
}

export async function saveUserSettings(userId: string, settings: UserSettings): Promise<UserSettings> {
  const res = await fetch(`${API_BASE}/api/settings/${userId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(settings),
  })

  if (!res.ok) {
    throw new Error('Failed to save user settings')
  }

  return res.json().then(data => data.settings)
}

export interface SearchResult {
  answer: string
  sources: Array<{
    title: string
    snippet: string
    url: string
  }>
  related_questions: string[]
}

export async function performSearch(query: string, searchEngine: string = 'serper'): Promise<SearchResult> {
  const res = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      search_engine: searchEngine,
    }),
  })

  if (!res.ok) {
    throw new Error('Failed to perform search')
  }

  return res.json()
}

export interface YouTubeResult {
  summary: string
  video_id?: string
  url: string
  metadata?: {
    title?: string
    channel_title?: string
    description?: string
    published_at?: string
    duration?: string
    view_count?: string
    thumbnail_url?: string
  }
  error?: string
}

export async function summarizeYouTube(url: string): Promise<YouTubeResult> {
  const res = await fetch(`${API_BASE}/api/youtube/summarize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      url,
    }),
  })

  if (!res.ok) {
    throw new Error('Failed to summarize YouTube video')
  }

  return res.json()
}
