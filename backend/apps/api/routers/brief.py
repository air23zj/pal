"""Brief endpoints"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional
import re

from packages.shared.schemas import BriefBundle, BriefItem, ModuleResult
from packages.database import get_db, crud
from packages.database.models import User

logger = logging.getLogger(__name__)

# Valid user_id pattern: alphanumeric, underscores, hyphens, 1-64 chars
USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')


def validate_user_id(user_id: str) -> str:
    """Validate user_id format to prevent injection attacks"""
    if not USER_ID_PATTERN.match(user_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id format. Must be 1-64 alphanumeric characters, underscores, or hyphens."
        )
    return user_id

router = APIRouter()


def _create_stub_brief(user_id: str = "u_dev") -> BriefBundle:
    """Create a stub BriefBundle for development"""
    now = datetime.now(timezone.utc)
    
    return BriefBundle(
        brief_id=f"brief_{now.isoformat()}",
        user_id=user_id,
        timezone="America/Los_Angeles",
        brief_date_local=now.strftime("%Y-%m-%d"),
        generated_at_utc=now.isoformat(),
        since_timestamp_utc=(now - timedelta(hours=24)).isoformat(),
        top_highlights=[],
        modules={
            "news": ModuleResult(
                status="ok",
                summary="No news configured yet. Configure RSS feeds to get started.",
                new_count=0,
                updated_count=0,
                items=[],
            ),
            "social_x": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
            "social_linkedin": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
            "research": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
            "podcasts": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
            "inbox": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
            "calendar": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
            "todos_notes": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
            "commute": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
            "weather": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
            "family": ModuleResult(status="skipped", summary="", new_count=0, updated_count=0, items=[]),
        },
        actions=[],
        evidence_log=[],
        run_metadata={
            "status": "ok",
            "latency_ms": 0,
            "cost_estimate_usd": 0.0,
            "agents_used": [],
            "warnings": ["Using stub data - database connected"],
        },
    )


@router.get("/latest")
async def get_latest_brief(
    user_id: str = Query(default="u_dev", description="User identifier"),
    db: Session = Depends(get_db)
) -> BriefBundle:
    """Get the latest brief bundle"""
    # Validate user_id format
    validate_user_id(user_id)

    # Ensure user exists
    crud.get_or_create_user(db, user_id=user_id)
    
    # Try to get latest brief from database
    db_brief = crud.get_latest_brief(db, user_id=user_id)
    
    if db_brief:
        # Return stored brief
        return BriefBundle(**db_brief.bundle_json)
    else:
        # Return stub and save it
        stub = _create_stub_brief(user_id=user_id)
        crud.create_brief_bundle(db, stub)
        return stub


async def _run_brief_generation(
    run_id: int,
    user_id: str,
    since_timestamp: datetime,
    user_preferences: dict,
):
    """
    Background task to run brief generation.

    This runs the orchestrator and stores the result in the database.
    """
    from packages.database.connection import SessionLocal
    from packages.orchestrator import run_brief_generation

    db = SessionLocal()
    try:
        # Update run status to running
        run = crud.get_brief_run(db, run_id=run_id)
        if run:
            run.status = "running"
            db.commit()

        # Run the orchestrator
        logger.info(f"Starting brief generation for user {user_id}, run {run_id}")
        brief_bundle = await run_brief_generation(
            user_id=user_id,
            user_preferences=user_preferences,
            since=since_timestamp,
            modules=["gmail", "calendar", "tasks"],  # Default modules
        )

        # Store the result
        crud.create_brief_bundle(db, brief_bundle)

        # Update run status
        if run:
            run.status = "completed"
            run.generated_at_utc = datetime.now(timezone.utc)
            run.latency_ms = brief_bundle.run_metadata.get("latency_ms", 0) if isinstance(brief_bundle.run_metadata, dict) else 0
            db.commit()

        logger.info(f"Brief generation completed for user {user_id}, run {run_id}")

    except Exception as e:
        logger.error(f"Brief generation failed for user {user_id}, run {run_id}: {e}", exc_info=True)
        # Update run status to error
        run = crud.get_brief_run(db, run_id=run_id)
        if run:
            run.status = "error"
            run.warnings_json = [str(e)]
            db.commit()
    finally:
        db.close()


@router.post("/run")
async def trigger_brief_run(
    background_tasks: BackgroundTasks,
    user_id: str = Query(default="u_dev", description="User identifier"),
    run_orchestrator: bool = Query(default=False, description="Actually run the orchestrator (slower)"),
    db: Session = Depends(get_db)
):
    """
    Trigger a new brief generation run.

    By default, creates a stub brief immediately. Set run_orchestrator=true
    to actually run the full orchestration pipeline (requires connectors to be configured).
    """
    # Validate user_id format
    validate_user_id(user_id)

    # Ensure user exists
    user = crud.get_or_create_user(db, user_id=user_id)

    # Determine since timestamp
    since_timestamp = user.last_brief_timestamp_utc or (datetime.now(timezone.utc) - timedelta(hours=24))

    # Create brief run record
    run = crud.create_brief_run(db, user_id=user_id, since_timestamp=since_timestamp)

    if run_orchestrator:
        # Schedule background task to run orchestrator
        user_preferences = user.settings_json or {}
        background_tasks.add_task(
            _run_brief_generation,
            run_id=run.id,
            user_id=user_id,
            since_timestamp=since_timestamp,
            user_preferences=user_preferences,
        )

        return {
            "run_id": run.id,
            "status": "queued",
            "message": "Brief generation started in background",
            "since_timestamp_utc": since_timestamp.isoformat(),
        }
    else:
        # Create stub brief immediately (for development)
        stub = _create_stub_brief(user_id=user_id)
        crud.create_brief_bundle(db, stub)

        # Update run status
        run.status = "completed"
        run.generated_at_utc = datetime.now(timezone.utc)
        db.commit()

        return {
            "run_id": run.id,
            "status": "completed",
            "message": "Stub brief created (use run_orchestrator=true for real data)",
            "since_timestamp_utc": since_timestamp.isoformat(),
        }


@router.get("/run/{run_id}")
async def get_run_status(
    run_id: int,
    db: Session = Depends(get_db)
):
    """Get brief run status"""
    run = crud.get_brief_run(db, run_id=run_id)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": run.id,
        "status": run.status,
        "since_timestamp_utc": run.since_timestamp_utc.isoformat() if run.since_timestamp_utc else None,
        "generated_at_utc": run.generated_at_utc.isoformat() if run.generated_at_utc else None,
        "latency_ms": run.latency_ms,
        "cost_estimate_usd": run.cost_estimate_usd,
        "warnings": run.warnings_json,
    }


@router.get("/{brief_id}")
async def get_brief_by_id(
    brief_id: str,
    db: Session = Depends(get_db)
) -> BriefBundle:
    """Get a specific brief by ID"""
    db_brief = crud.get_brief_by_id(db, brief_id=brief_id)
    
    if not db_brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    
    return BriefBundle(**db_brief.bundle_json)
