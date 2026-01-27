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
import logging
import os
from enum import Enum

logger = logging.getLogger(__name__)

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
                logger.error(f"Progress callback error: {e}")
    
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
                     Options: "gmail", "calendar", "tasks", "keep", "twitter", "linkedin", "research", "news", "flights", "dining", "travel", "local", "shopping"
        
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
        Fetch data from all requested modules in parallel.
        
        Returns dict mapping module name to raw data.
        """
        tasks = []
        module_names = []
        
        for module in modules:
            if module == "gmail":
                from packages.connectors.gmail import GmailConnector
                connector = GmailConnector()
                if connector.is_available():
                    tasks.append(connector.fetch(since=since))
                module_names.append("gmail")
                else:
                    self.warnings.append("Gmail module not available - Google credentials not configured")
                
            elif module == "calendar":
                from packages.connectors.calendar import CalendarConnector
                connector = CalendarConnector()
                if connector.is_available():
                    tasks.append(connector.fetch(since=since))
                module_names.append("calendar")
                else:
                    self.warnings.append("Calendar module not available - Google credentials not configured")
                
            elif module == "tasks":
                from packages.connectors.tasks import TasksConnector
                connector = TasksConnector()
                if connector.is_available():
                    tasks.append(connector.fetch(since=since))
                module_names.append("tasks")
                else:
                    self.warnings.append("Tasks module not available - Google credentials not configured")

            elif module == "keep":
                from packages.connectors.keep import KeepConnector
                connector = KeepConnector()
                if connector.is_available():
                    tasks.append(connector.fetch(since=since))
                    module_names.append("keep")
                else:
                    self.warnings.append("Keep module not available - Google credentials not configured")
                
            elif module == "twitter":
                self.warnings.append("Twitter integration is using experimental BrowserAgent setup")
                from packages.agents.twitter_agent import TwitterAgent
                async def fetch_twitter():
                    agent = TwitterAgent()
                    async with agent:
                        return await agent.fetch_feed()
                tasks.append(fetch_twitter())
                module_names.append("twitter")

            elif module == "linkedin":
                self.warnings.append("LinkedIn integration is using experimental BrowserAgent setup")
                from packages.agents.linkedin_agent import LinkedInAgent
                async def fetch_linkedin():
                    agent = LinkedInAgent()
                    async with agent:
                        return await agent.fetch_feed()
                tasks.append(fetch_linkedin())
                module_names.append("linkedin")
                
            elif module == "research":
                from packages.connectors.research import ResearchConnector
                # Pass API key directly if available in preferences
                serper_key = self.user_preferences.get('serper_key') or os.getenv('SERPER_SEARCH_API_KEY')
                connector = ResearchConnector(api_key=serper_key)
                if connector.is_available():
                    tasks.append(connector.fetch_messages(since=since, user_preferences=self.user_preferences))
                    module_names.append("research")
                else:
                    self.warnings.append("Research module not available - SerpApi key not configured")

            elif module == "news":
                from packages.connectors.news import NewsConnector
                # Pass API key directly if available in preferences
                serpapi_key = self.user_preferences.get('serpapi_key') or os.getenv('SERPAPI_API_KEY')
                connector = NewsConnector(api_key=serpapi_key)
                if connector.is_available():
                    tasks.append(connector.fetch(since=since, user_preferences=self.user_preferences))
                    module_names.append("news")
                else:
                    self.warnings.append("News module not available - SerpApi key not configured")

            elif module == "flights":
                from packages.connectors.flights import FlightsConnector
                # Pass API key directly if available in preferences
                serpapi_key = self.user_preferences.get('serpapi_key') or os.getenv('SERPAPI_API_KEY')
                connector = FlightsConnector(api_key=serpapi_key)
                if connector.is_available():
                    tasks.append(connector.fetch(since=since, user_preferences=self.user_preferences))
                    module_names.append("flights")
                else:
                    self.warnings.append("Flights module not available - SerpApi key not configured")

            elif module == "dining":
                from packages.connectors.dining import DiningConnector
                # Pass API key directly if available in preferences
                serpapi_key = self.user_preferences.get('serpapi_key') or os.getenv('SERPAPI_API_KEY')
                connector = DiningConnector(api_key=serpapi_key)
                if connector.is_available():
                    tasks.append(connector.fetch(since=since, user_preferences=self.user_preferences))
                    module_names.append("dining")
                else:
                    self.warnings.append("Dining module not available - SerpApi key not configured")

            elif module == "travel":
                from packages.connectors.travel import TravelConnector
                # Pass API key directly if available in preferences
                serpapi_key = self.user_preferences.get('serpapi_key') or os.getenv('SERPAPI_API_KEY')
                connector = TravelConnector(api_key=serpapi_key)
                if connector.is_available():
                    tasks.append(connector.fetch(since=since, user_preferences=self.user_preferences))
                    module_names.append("travel")
                else:
                    self.warnings.append("Travel module not available - SerpApi key not configured")

            elif module == "local":
                from packages.connectors.local import LocalConnector
                # Pass API key directly if available in preferences
                serpapi_key = self.user_preferences.get('serpapi_key') or os.getenv('SERPAPI_API_KEY')
                connector = LocalConnector(api_key=serpapi_key)
                if connector.is_available():
                    tasks.append(connector.fetch(since=since, user_preferences=self.user_preferences))
                    module_names.append("local")
                else:
                    self.warnings.append("Local module not available - SerpApi key not configured")

            elif module == "shopping":
                from packages.connectors.shopping import ShoppingConnector
                # Pass API key directly if available in preferences
                serpapi_key = self.user_preferences.get('serpapi_key') or os.getenv('SERPAPI_API_KEY')
                connector = ShoppingConnector(api_key=serpapi_key)
                if connector.is_available():
                    tasks.append(connector.fetch(since=since, user_preferences=self.user_preferences))
                    module_names.append("shopping")
                else:
                    self.warnings.append("Shopping module not available - SerpApi key not configured")

            else:
                self.warnings.append(f"Unknown module: {module}")
        
        results = {}
        if not tasks:
            return results
            
        # Execute all fetches in parallel
        fetch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(module_names, fetch_results):
            if isinstance(result, Exception):
                self.errors.append(f"{name}: {str(result)}")
                results[name] = []
            elif hasattr(result, 'items'):  # ConnectorResult
                results[name] = result.items
            else:  # Raw list from agents
                results[name] = result
        
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

                elif source == "research":
                    # Research items are already BriefItem objects
                    for item in data:
                        if isinstance(item, BriefItem):
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
        for source, data in raw_data.items():
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, BriefItem):
                        # For sources that return BriefItem objects (like research),
                        # create a dict representation for fingerprinting
                        item_dict = {
                            'title': item.title,
                            'summary': item.summary,
                            'timestamp_utc': item.timestamp_utc,
                            'source_id': item.item_ref,
                            'url': getattr(item, 'url', None),
                            'metadata': item.metadata,
                        }
                        all_raw_items.append(item_dict)
                    else:
                        # Raw dict data from other connectors
                        all_raw_items.append(item)
        
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
            
            # Create module summaries in parallel
            module_summary_tasks = []
            module_sources = []
            
            for source, module_result in module_results.items():
                if module_result.items:
                    module_summary_tasks.append(
                        self._synthesizer.create_module_summary(
                            module_name=source,
                            items=module_result.items,
                            new_count=module_result.new_count,
                            updated_count=module_result.updated_count,
                        )
                    )
                    module_sources.append(source)
            
            if module_summary_tasks:
                summaries = await asyncio.gather(*module_summary_tasks, return_exceptions=True)
                module_summaries = {}
                for source, summary in zip(module_sources, summaries):
                    if isinstance(summary, Exception):
                        self.warnings.append(f"Summary failed for {source}: {summary}")
                        module_summaries[source] = f"Update for {source}"
                    else:
                        module_summaries[source] = summary
            else:
                module_summaries = {}
            
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
