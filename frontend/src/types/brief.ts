/**
 * Morning Brief AGI - TypeScript Type Definitions
 * These types match the Python Pydantic schemas
 */

export type NoveltyLabel = 'NEW' | 'UPDATED' | 'REPEAT' | 'LOW_SIGNAL'
export type ModuleStatus = 'ok' | 'degraded' | 'error' | 'skipped'
export type EvidenceKind = 'url' | 'snippet' | 'file'

export interface Entity {
  kind: string // 'topic' | 'person' | 'project' | 'org'
  key: string
}

export interface NoveltyInfo {
  label: NoveltyLabel
  reason: string
  first_seen_utc: string
  last_updated_utc?: string
  seen_count: number
}

export interface RankingScores {
  relevance_score: number
  urgency_score: number
  credibility_score: number
  impact_score: number
  actionability_score: number
  final_score: number
}

export interface Evidence {
  kind: EvidenceKind
  title: string
  url?: string
  text?: string
}

export interface SuggestedAction {
  type: string
  label: string
  payload?: Record<string, any>
}

export interface BriefItem {
  item_ref: string
  source: string
  type: string
  timestamp_utc: string
  source_id?: string
  url?: string | null

  title: string
  summary: string
  why_it_matters: string
  entities: Entity[]

  novelty: NoveltyInfo
  ranking: RankingScores

  evidence: Evidence[]
  suggested_actions: SuggestedAction[]
}

export interface ModuleResult {
  status: ModuleStatus
  summary: string
  new_count: number
  updated_count: number
  items: BriefItem[]
}

export interface Action {
  action_id: string
  type: string
  label: string
  payload: Record<string, any>
}

export interface EvidenceLogEntry {
  item_ref: string
  evidence: Evidence[]
}

export interface RunMetadata {
  status: string
  latency_ms: number
  cost_estimate_usd: number
  agents_used: string[]
  warnings: string[]
}

export interface BriefBundle {
  brief_id: string
  user_id: string
  timezone: string
  brief_date_local: string
  generated_at_utc: string
  since_timestamp_utc: string

  top_highlights: BriefItem[]

  // Modules are keyed by source name (gmail, calendar, tasks, etc.)
  modules: Record<string, ModuleResult>

  actions: Action[]
  evidence_log: EvidenceLogEntry[]
  run_metadata?: RunMetadata
}
