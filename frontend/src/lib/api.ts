/**
 * API client for Morning Brief backend
 */
import { BriefBundle } from '@/types/brief'

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
