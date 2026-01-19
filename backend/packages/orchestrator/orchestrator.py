"""
Brief generation orchestrator.

Coordinates all components to generate a complete brief:
1. Fetch data from connectors
2. Normalize to BriefItems
3. Apply novelty detection
4. Rank by importance
5. Synthesize with LLM
6. Package into BriefBundle
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
import asyncio
from enum import Enum

from packages.shared.schemas import BriefBundle, ModuleResult, BriefItem
from packages.memory import MemoryManager, NoveltyDetector, detect_novelty_for_items
from packages.ranking import Ranker
from packages.editor import BriefSynthesizer, get_llm_client


class BriefStatus(str, Enum):
    """Brief generation status"""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "ok"
    DEGRADED = "degraded"  # Partial failures
    ERROR = "error"


class BriefOrchestrator:
    """
    Orchestrates the complete brief generation pipeline.
    
    Connects all components and handles the end-to-end flow.
    """
    
    def __init__(
        self,
        user_id: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None,
    ):
        """
        Initialize orchestrator.
        
        Args:
            user_id: User identifier
            user_preferences: User preferences for ranking/synthesis
            progress_callback: Optional callback for progress updates
                               Signature: callback(stage: str, progress: float, message: str)
        """
        self.user_id = user_id
        self.user_preferences = user_preferences or {}
        self.progress_callback = progress_callback
        
        # Initialize components
        self.memory_manager = MemoryManager()
        self.novelty_detector = NoveltyDetector(self.memory_manager)
        self.ranker = Ranker(user_preferences=self.user_preferences)
        
        # LLM synthesizer (initialized lazily)
        self._synthesizer = None
        
        # Track warnings and errors
        self.warnings = []
        self.errors = []
    
    def _report_progress(self, stage: str, progress: float, message: str):
        """Report progress to callback"""
        if self.progress_callback:
            try:
                self.progress_callback(stage, progress, message)
            except Exception as e:
                print(f"Progress callback error: {e}")
    
    async def generate_brief(
        self,
        since: Optional[datetime] = None,
        modules: Optional[List[str]] = None,
    ) -> BriefBundle:
        """
        Generate a complete brief.
        
        Args:
            since: Fetch items since this timestamp (default: last 24h)
            modules: List of modules to include (default: all)
                     Options: "gmail", "calendar", "tasks", "twitter", "linkedin"
        
        Returns:
            Complete BriefBundle
        """
        start_time = datetime.now(timezone.utc)
        
        if since is None:
            since = start_time - timedelta(hours=24)
        
        if modules is None:
            modules = ["gmail", "calendar", "tasks"]  # Social agents optional
        
        self._report_progress("init", 0.0, "Starting brief generation")
        
        try:
            # Step 1: Fetch data from connectors
            self._report_progress("fetch", 0.1, "Fetching data from connectors")
            raw_data = await self._fetch_all_data(modules, since)
            
            # Step 2: Normalize to BriefItems
            self._report_progress("normalize", 0.3, "Normalizing data")
            all_items = self._normalize_all_data(raw_data)
            
            # Step 3: Apply novelty detection
            self._report_progress("novelty", 0.4, "Detecting novelty")
            items_with_novelty = await self._apply_novelty_detection(all_items, raw_data)
            
            # Filter to only NEW and UPDATED
            new_and_updated = [
                item for item in items_with_novelty
                if item.novelty and item.novelty.label in ["NEW", "UPDATED"]
            ]
            
            # Step 4: Rank by importance
            self._report_progress("ranking", 0.5, "Ranking items by importance")
            ranked_items = self.ranker.rank_items(new_and_updated)
            
            # Step 5: Select top items per module + highlights
            self._report_progress("selection", 0.6, "Selecting top items")
            module_results, top_highlights = self._organize_by_module(ranked_items)
            
            # Step 6: Synthesize with LLM
            self._report_progress("synthesis", 0.7, "Generating explanations")
            final_items, module_summaries = await self._synthesize_brief(
                ranked_items,
                module_results
            )
            
            # Step 7: Package into BriefBundle
            self._report_progress("packaging", 0.9, "Packaging brief")
            brief_bundle = self._create_brief_bundle(
                final_items=final_items,
                module_results=module_results,
                module_summaries=module_summaries,
                top_highlights=top_highlights,
                since=since,
                start_time=start_time,
            )
            
            self._report_progress("complete", 1.0, "Brief generation complete")
            
            return brief_bundle
            
        except Exception as e:
            self._report_progress("error", 1.0, f"Error: {e}")
            raise
    
    async def _fetch_all_data(
        self,
        modules: List[str],
        since: datetime,
    ) -> Dict[str, Any]:
        """
        Fetch data from all requested modules.
        
        Returns dict mapping module name to raw data.
        """
        results = {}
        
        for module in modules:
            try:
                if module == "gmail":
                    # Import here to avoid dependency issues
                    from packages.connectors.gmail import GmailConnector
                    connector = GmailConnector()
                    data = connector.fetch_messages(since=since)
                    results["gmail"] = data
                    
                elif module == "calendar":
                    from packages.connectors.calendar import CalendarConnector
                    connector = CalendarConnector()
                    data = connector.fetch_events(since=since)
                    results["calendar"] = data
                    
                elif module == "tasks":
                    from packages.connectors.tasks import TasksConnector
                    connector = TasksConnector()
                    data = connector.fetch_tasks()
                    results["tasks"] = data
                    
                elif module == "twitter":
                    # Social agents require special handling
                    self.warnings.append(f"Twitter agent requires manual setup")
                    results["twitter"] = []
                    
                elif module == "linkedin":
                    self.warnings.append(f"LinkedIn agent requires manual setup")
                    results["linkedin"] = []
                    
                else:
                    self.warnings.append(f"Unknown module: {module}")
                    
            except Exception as e:
                self.errors.append(f"{module}: {str(e)}")
                results[module] = []  # Continue with empty results
        
        return results
    
    def _normalize_all_data(self, raw_data: Dict[str, Any]) -> List[BriefItem]:
        """Normalize all raw data to BriefItems"""
        from packages.normalizer.normalizer import Normalizer
        
        all_items = []
        
        for source, data in raw_data.items():
            try:
                if not data:
                    continue
                
                if source == "gmail":
                    for item_data in data:
                        item = Normalizer.normalize_gmail_item(item_data)
                        all_items.append(item)
                        
                elif source == "calendar":
                    for item_data in data:
                        item = Normalizer.normalize_calendar_item(item_data)
                        all_items.append(item)
                        
                elif source == "tasks":
                    for item_data in data:
                        item = Normalizer.normalize_task_item(item_data)
                        all_items.append(item)
                        
                elif source in ["twitter", "linkedin"]:
                    for item_data in data:
                        item = Normalizer.normalize_social_post(item_data, source)
                        all_items.append(item)
                        
            except Exception as e:
                self.errors.append(f"Normalization error in {source}: {e}")
        
        return all_items
    
    async def _apply_novelty_detection(
        self,
        items: List[BriefItem],
        raw_data: Dict[str, Any],
    ) -> List[BriefItem]:
        """Apply novelty detection to items"""
        # Flatten raw data for novelty detection
        all_raw_items = []
        for data in raw_data.values():
            if isinstance(data, list):
                all_raw_items.extend(data)
        
        # Detect novelty
        items_with_novelty = self.novelty_detector.detect_novelty_batch(
            user_id=self.user_id,
            items=items,
            items_data=all_raw_items if all_raw_items else None,
        )
        
        return items_with_novelty
    
    def _organize_by_module(
        self,
        ranked_items: List[BriefItem],
    ) -> tuple[Dict[str, ModuleResult], List[BriefItem]]:
        """
        Organize items by module and select highlights.

        Returns:
            (module_results, top_highlights)
        """
        # Group by source
        by_source: Dict[str, List[BriefItem]] = {}
        for item in ranked_items:
            if item.source not in by_source:
                by_source[item.source] = []
            by_source[item.source].append(item)

        # Apply caps per module
        module_results = {}
        for source, items in by_source.items():
            capped_items = items[:8]  # Max 8 per module

            # Count novelty
            new_count = sum(1 for item in capped_items if item.novelty and item.novelty.label == "NEW")
            updated_count = sum(1 for item in capped_items if item.novelty and item.novelty.label == "UPDATED")

            # Create summary based on counts
            summary = f"{new_count} new"
            if updated_count > 0:
                summary += f", {updated_count} updated"

            module_results[source] = ModuleResult(
                status="ok",
                summary=summary,
                new_count=new_count,
                updated_count=updated_count,
                items=capped_items,
            )

        # Select top highlights (across all modules)
        top_highlights = self.ranker.select_top_highlights(ranked_items, max_count=5)

        return module_results, top_highlights
    
    async def _synthesize_brief(
        self,
        ranked_items: List[BriefItem],
        module_results: Dict[str, ModuleResult],
    ) -> tuple[List[BriefItem], Dict[str, str]]:
        """
        Synthesize brief with LLM.
        
        Returns:
            (items_with_why_it_matters, module_summaries)
        """
        try:
            # Initialize synthesizer lazily
            if not self._synthesizer:
                llm = get_llm_client()
                self._synthesizer = BriefSynthesizer(
                    llm_client=llm,
                    user_preferences=self.user_preferences,
                )
            
            # Add "why it matters" to top items
            top_items = ranked_items[:20]  # Limit LLM calls
            items_with_why = await self._synthesizer.synthesize_items(top_items)
            
            # Create module summaries
            module_summaries = {}
            for source, module_result in module_results.items():
                if module_result.items:
                    summary = await self._synthesizer.create_module_summary(
                        module_name=module_result.module_name,
                        items=module_result.items,
                        new_count=module_result.new_count,
                        updated_count=module_result.updated_count,
                    )
                    module_summaries[source] = summary
            
            # Update items in ranked_items with synthesized versions
            synthesized_by_ref = {item.item_ref: item for item in items_with_why}
            final_items = []
            for item in ranked_items:
                if item.item_ref in synthesized_by_ref:
                    final_items.append(synthesized_by_ref[item.item_ref])
                else:
                    final_items.append(item)
            
            return final_items, module_summaries
            
        except Exception as e:
            self.warnings.append(f"LLM synthesis failed: {e}")
            # Continue without synthesis
            return ranked_items, {}
    
    def _create_brief_bundle(
        self,
        final_items: List[BriefItem],
        module_results: Dict[str, ModuleResult],
        module_summaries: Dict[str, str],
        top_highlights: List[BriefItem],
        since: datetime,
        start_time: datetime,
    ) -> BriefBundle:
        """Create final BriefBundle"""
        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        # Update module summaries from LLM
        for source, module_result in module_results.items():
            if source in module_summaries:
                module_result.summary = module_summaries[source]

        # Determine status
        if self.errors:
            status = BriefStatus.ERROR if not module_results else BriefStatus.DEGRADED
        elif self.warnings:
            status = BriefStatus.DEGRADED
        else:
            status = BriefStatus.SUCCESS

        # Get user timezone (default to UTC)
        user_tz = self.user_preferences.get("timezone", "UTC")

        return BriefBundle(
            brief_id=f"brief_{int(start_time.timestamp())}",
            user_id=self.user_id,
            timezone=user_tz,
            brief_date_local=start_time.strftime("%Y-%m-%d"),
            generated_at_utc=start_time.isoformat(),
            since_timestamp_utc=since.isoformat(),
            top_highlights=top_highlights,
            modules=module_results,  # Dict[str, ModuleResult] as per schema
            actions=[],
            evidence_log=[],
            run_metadata={
                "status": status.value,
                "latency_ms": latency_ms,
                "cost_estimate_usd": 0.0,
                "agents_used": list(module_results.keys()),
                "warnings": self.warnings if self.warnings else [],
            },
        )


async def run_brief_generation(
    user_id: str,
    user_preferences: Optional[Dict[str, Any]] = None,
    since: Optional[datetime] = None,
    modules: Optional[List[str]] = None,
    progress_callback: Optional[Callable] = None,
) -> BriefBundle:
    """
    Convenience function to run brief generation.
    
    Args:
        user_id: User identifier
        user_preferences: User preferences
        since: Fetch items since this time
        modules: List of modules to include
        progress_callback: Optional progress callback
        
    Returns:
        Complete BriefBundle
    """
    orchestrator = BriefOrchestrator(
        user_id=user_id,
        user_preferences=user_preferences,
        progress_callback=progress_callback,
    )
    
    return await orchestrator.generate_brief(since=since, modules=modules)
