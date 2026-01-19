"""
Morning Brief AGI - Core Data Schemas
These schemas define the contract between backend and frontend.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime


# ============================================================================
# Core Item Schemas
# ============================================================================

class Entity(BaseModel):
    """Entity reference (person, topic, project, etc.)"""
    kind: str = Field(..., description="Entity type: topic, person, project, org")
    key: str = Field(..., description="Entity identifier")


class NoveltyInfo(BaseModel):
    """Novelty detection information"""
    label: Literal["NEW", "UPDATED", "REPEAT", "LOW_SIGNAL"]
    reason: str = Field(..., description="Why this novelty label was assigned")
    first_seen_utc: str = Field(..., description="ISO timestamp when first seen")


class RankingScores(BaseModel):
    """Importance ranking scores"""
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    urgency_score: float = Field(..., ge=0.0, le=1.0)
    credibility_score: float = Field(..., ge=0.0, le=1.0)
    actionability_score: float = Field(..., ge=0.0, le=1.0)
    final_score: float = Field(..., ge=0.0, le=1.0)


class Evidence(BaseModel):
    """Evidence/source link"""
    kind: Literal["url", "snippet", "file"]
    title: str
    url: Optional[str] = None
    text: Optional[str] = None


class SuggestedAction(BaseModel):
    """Suggested action for an item"""
    type: str = Field(..., description="Action type: bookmark, add_task, reply, etc.")
    label: str = Field(..., description="Human-readable action label")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Action-specific payload data")


class BriefItem(BaseModel):
    """
    Uniform item structure across all sources.
    This is THE core data structure.
    """
    item_ref: str = Field(..., description="Stable item ID")
    source: str = Field(..., description="Source: arxiv, gmail, x, linkedin, etc.")
    type: str = Field(..., description="Type: paper, email, post, event, etc.")
    timestamp_utc: str = Field(..., description="ISO timestamp")
    
    title: str
    summary: str
    why_it_matters: str = Field(..., description="Personalized importance explanation")
    entities: List[Entity] = Field(default_factory=list)
    
    novelty: NoveltyInfo
    ranking: RankingScores
    
    evidence: List[Evidence] = Field(default_factory=list)
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)


# ============================================================================
# Module Result Schema
# ============================================================================

class ModuleResult(BaseModel):
    """
    Uniform module response structure.
    All modules MUST return this shape.
    """
    status: Literal["ok", "degraded", "error", "skipped"]
    summary: str = Field(..., description="Module summary line")
    new_count: int = Field(..., ge=0)
    updated_count: int = Field(..., ge=0)
    items: List[BriefItem] = Field(default_factory=list)


# ============================================================================
# Action Schema
# ============================================================================

class Action(BaseModel):
    """Suggested action at bundle level"""
    action_id: str
    type: str = Field(..., description="create_task, send_email, block_calendar, etc.")
    label: str = Field(..., description="Human-readable label")
    payload: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Evidence Log Schema
# ============================================================================

class EvidenceLogEntry(BaseModel):
    """Evidence log entry for an item"""
    item_ref: str
    evidence: List[Evidence]


# ============================================================================
# Brief Bundle Schema (Top-Level Response)
# ============================================================================

class BriefBundle(BaseModel):
    """
    Top-level brief bundle response.
    This is what the frontend receives.
    """
    brief_id: str
    user_id: str
    timezone: str
    brief_date_local: str = Field(..., description="YYYY-MM-DD in user's timezone")
    generated_at_utc: str = Field(..., description="ISO timestamp")
    since_timestamp_utc: str = Field(..., description="ISO timestamp - start of delta")
    
    top_highlights: List[BriefItem] = Field(default_factory=list, max_length=5)
    
    modules: Dict[str, ModuleResult] = Field(
        ...,
        description="Module results keyed by module name"
    )
    
    actions: List[Action] = Field(default_factory=list)
    evidence_log: List[EvidenceLogEntry] = Field(default_factory=list)
    
    run_metadata: Dict[str, Any] = Field(
        ...,
        description="Run statistics and metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "brief_id": "brief_2026-01-18T06:03:00-08:00",
                "user_id": "u_123",
                "timezone": "America/Los_Angeles",
                "brief_date_local": "2026-01-18",
                "generated_at_utc": "2026-01-18T14:03:05Z",
                "since_timestamp_utc": "2026-01-17T14:00:00Z",
                "top_highlights": [],
                "modules": {
                    "news": {
                        "status": "ok",
                        "summary": "2 major updates",
                        "new_count": 2,
                        "updated_count": 0,
                        "items": []
                    }
                },
                "actions": [],
                "evidence_log": [],
                "run_metadata": {
                    "status": "ok",
                    "latency_ms": 42000,
                    "cost_estimate_usd": 0.42,
                    "agents_used": ["news_agent"],
                    "warnings": []
                }
            }
        }
