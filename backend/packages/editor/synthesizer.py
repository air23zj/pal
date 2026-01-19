"""
Brief synthesizer - uses LLM to generate "why it matters" and summaries
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

from packages.shared.schemas import BriefItem, ModuleResult
from .llm_client import LLMClient, get_llm_client
from .prompts import (
    SYSTEM_PROMPT,
    WHY_IT_MATTERS_PROMPT,
    MODULE_SUMMARY_PROMPT,
    COMPRESS_SUMMARY_PROMPT,
)


class BriefSynthesizer:
    """
    Synthesizes brief content using LLM.
    Adds "why it matters" to items and creates module summaries.
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize synthesizer.
        
        Args:
            llm_client: LLM client to use (default: auto-detect)
            user_preferences: User preferences for personalization
        """
        self.llm = llm_client or get_llm_client()
        self.preferences = user_preferences or {}
    
    async def add_why_it_matters(self, item: BriefItem) -> BriefItem:
        """
        Add "why it matters" explanation to a brief item.
        
        Args:
            item: BriefItem to enhance
            
        Returns:
            Item with updated why_it_matters field
        """
        # Format prompt with item data
        prompt = WHY_IT_MATTERS_PROMPT.format(
            title=item.title,
            summary=item.summary,
            source=item.source,
            type=item.type,
            timestamp=item.timestamp_utc,
            user_topics=", ".join(self.preferences.get('topics', ['general'])),
            vip_people=", ".join(self.preferences.get('vip_people', ['none'])),
            projects=", ".join(self.preferences.get('projects', ['none'])),
            relevance_score=item.ranking.relevance_score if item.ranking else 0.5,
            urgency_score=item.ranking.urgency_score if item.ranking else 0.5,
        )
        
        try:
            # Generate explanation
            why_it_matters = await self.llm.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                max_tokens=150,
                temperature=0.7,
            )
            
            # Update item
            item.why_it_matters = why_it_matters.strip()
            
        except Exception as e:
            logger.warning(f"Error generating 'why it matters': {e}")
            # Fallback to default explanation
            item.why_it_matters = self._generate_fallback_why_it_matters(item)
        
        return item
    
    async def synthesize_items(self, items: List[BriefItem]) -> List[BriefItem]:
        """
        Add "why it matters" to multiple items in parallel.
        
        Args:
            items: List of BriefItems
            
        Returns:
            Items with why_it_matters added
        """
        # Process items in parallel (with limit to avoid rate limits)
        batch_size = 5
        synthesized = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            tasks = [self.add_why_it_matters(item) for item in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch: {result}")
                else:
                    synthesized.append(result)
            
            # Small delay between batches
            if i + batch_size < len(items):
                await asyncio.sleep(0.5)
        
        return synthesized
    
    async def create_module_summary(
        self,
        module_name: str,
        items: List[BriefItem],
        new_count: int,
        updated_count: int,
    ) -> str:
        """
        Create a summary for a module.
        
        Args:
            module_name: Name of the module
            items: Items in this module
            new_count: Number of new items
            updated_count: Number of updated items
            
        Returns:
            Module summary text
        """
        if not items:
            return f"No new updates in {module_name}."
        
        # Count urgent items
        urgent_count = sum(
            1 for item in items 
            if item.ranking and item.ranking.urgency_score > 0.7
        )
        
        # Create items summary
        items_summary = "\n".join([
            f"- {item.title} (score: {item.ranking.final_score:.2f})"
            for item in items[:5]  # Top 5 for context
        ])
        
        # Format prompt
        prompt = MODULE_SUMMARY_PROMPT.format(
            module_name=module_name,
            item_count=len(items),
            items_summary=items_summary,
            new_count=new_count,
            updated_count=updated_count,
            urgent_count=urgent_count,
        )
        
        try:
            summary = await self.llm.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                max_tokens=100,
                temperature=0.7,
            )
            return summary.strip()
            
        except Exception as e:
            logger.warning(f"Error generating module summary: {e}")
            # Fallback summary
            return self._generate_fallback_module_summary(
                module_name, len(items), new_count, urgent_count
            )
    
    def _generate_fallback_why_it_matters(self, item: BriefItem) -> str:
        """Generate fallback explanation when LLM fails"""
        if item.type == "email":
            return "New email requiring your attention."
        elif item.type == "event":
            return "Upcoming event on your calendar."
        elif item.type == "task":
            return "Pending task that needs completion."
        else:
            return "New item for your review."
    
    def _generate_fallback_module_summary(
        self,
        module_name: str,
        item_count: int,
        new_count: int,
        urgent_count: int,
    ) -> str:
        """Generate fallback summary when LLM fails"""
        parts = [f"{new_count} new"]
        if urgent_count > 0:
            parts.append(f"{urgent_count} urgent")
        
        return f"{module_name}: {', '.join(parts)} items."


async def synthesize_brief(
    items: List[BriefItem],
    modules: Dict[str, ModuleResult],
    user_preferences: Optional[Dict[str, Any]] = None,
    llm_client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """
    Convenience function to synthesize a complete brief.
    
    Args:
        items: All brief items
        modules: Module results
        user_preferences: User preferences
        llm_client: Optional LLM client
        
    Returns:
        Dict with synthesized content
    """
    synthesizer = BriefSynthesizer(
        llm_client=llm_client,
        user_preferences=user_preferences,
    )
    
    # Synthesize items
    synthesized_items = await synthesizer.synthesize_items(items)
    
    # Create module summaries
    module_summaries = {}
    for module_name, module_result in modules.items():
        if module_result.items:
            summary = await synthesizer.create_module_summary(
                module_name=module_name,
                items=module_result.items,
                new_count=module_result.new_count,
                updated_count=module_result.updated_count,
            )
            module_summaries[module_name] = summary
    
    return {
        "items": synthesized_items,
        "module_summaries": module_summaries,
    }
