#!/usr/bin/env python3
"""
Test brief synthesis system with LLM
"""
import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load environment variables from .env file
def load_env_file():
    """Load .env file if it exists"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env_file()

from packages.shared.schemas import BriefItem, Entity, NoveltyInfo, RankingScores, Evidence, SuggestedAction, ModuleResult
from packages.editor import get_llm_client, BriefSynthesizer


def create_sample_items() -> list[BriefItem]:
    """Create sample BriefItems for testing"""
    now = datetime.now(timezone.utc)
    
    items = [
        # Urgent meeting
        BriefItem(
            item_ref="item_1",
            source="calendar",
            type="event",
            timestamp_utc=(now + timedelta(minutes=30)).isoformat(),
            title="Q4 Strategy Meeting with CEO",
            summary="Starts at 2:00 PM with 10 attendees including CFO and board members",
            why_it_matters="pending",
            entities=[
                Entity(kind="person", key="ceo@company.com"),
                Entity(kind="project", key="q4-strategy"),
            ],
            novelty=NoveltyInfo(label="NEW", reason="test", first_seen_utc=now.isoformat()),
            ranking=RankingScores(
                relevance_score=0.80,
                urgency_score=1.00,
                credibility_score=0.95,
                impact_score=0.90,
                actionability_score=0.20,
                final_score=0.78
            ),
            evidence=[],
            suggested_actions=[],
        ),
        
        # Important email
        BriefItem(
            item_ref="item_2",
            source="gmail",
            type="email",
            timestamp_utc=(now - timedelta(hours=2)).isoformat(),
            title="Budget Approval Needed - from boss@company.com",
            summary="Need your sign-off on Q1 budget allocation by EOD. Includes $50K for new initiative.",
            why_it_matters="pending",
            entities=[Entity(kind="person", key="boss@company.com")],
            novelty=NoveltyInfo(label="NEW", reason="test", first_seen_utc=now.isoformat()),
            ranking=RankingScores(
                relevance_score=0.65,
                urgency_score=0.70,
                credibility_score=0.90,
                impact_score=0.80,
                actionability_score=0.60,
                final_score=0.68
            ),
            evidence=[],
            suggested_actions=[],
        ),
    ]
    
    return items


async def main():
    """Test synthesis system"""
    print("🧪 Testing Brief Synthesis System\n")
    
    # Check for LLM availability
    print("1. Checking LLM Availability...")
    try:
        llm = get_llm_client()
        print(f"   ✅ LLM available: {llm.__class__.__name__}")
        print(f"   Model: {llm.model}\n")
    except Exception as e:
        print(f"   ❌ No LLM available: {e}\n")
        print("   To test synthesis, you need either:")
        print("   - Ollama running locally: `ollama serve`")
        print("   - Claude API key: export ANTHROPIC_API_KEY=sk-...")
        print("   - OpenAI API key: export OPENAI_API_KEY=sk-...\n")
        return
    
    # Test basic generation
    print("2. Testing Basic Generation...")
    try:
        response = await llm.generate(
            prompt="Say hello in one sentence.",
            max_tokens=50,
        )
        print(f"   Response: {response}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return
    
    # Create sample items
    print("3. Creating Sample Brief Items...")
    items = create_sample_items()
    print(f"   Created {len(items)} sample items\n")
    
    # Define user preferences
    user_preferences = {
        'topics': ['budget', 'strategy', 'Q4', 'initiatives'],
        'vip_people': ['ceo@company.com', 'boss@company.com'],
        'projects': ['q4-strategy', 'new-initiative'],
    }
    
    print("4. User Preferences:")
    print(f"   Topics: {user_preferences['topics']}")
    print(f"   VIPs: {user_preferences['vip_people']}")
    print(f"   Projects: {user_preferences['projects']}\n")
    
    # Create synthesizer
    print("5. Synthesizing 'Why It Matters'...")
    synthesizer = BriefSynthesizer(
        llm_client=llm,
        user_preferences=user_preferences,
    )
    
    # Synthesize items
    synthesized = await synthesizer.synthesize_items(items)
    
    print("   Results:\n")
    for i, item in enumerate(synthesized, 1):
        print(f"   Item {i}: {item.title}")
        print(f"   Score: {item.ranking.final_score:.2f}")
        print(f"   Why it matters: {item.why_it_matters}")
        print()
    
    # Test module summary
    print("6. Testing Module Summary...")
    calendar_items = [item for item in synthesized if item.source == "calendar"]
    if calendar_items:
        summary = await synthesizer.create_module_summary(
            module_name="Calendar",
            items=calendar_items,
            new_count=len(calendar_items),
            updated_count=0,
        )
        print(f"   Calendar Summary: {summary}\n")
    
    email_items = [item for item in synthesized if item.source == "gmail"]
    if email_items:
        summary = await synthesizer.create_module_summary(
            module_name="Inbox",
            items=email_items,
            new_count=len(email_items),
            updated_count=0,
        )
        print(f"   Inbox Summary: {summary}\n")
    
    print("✅ Brief synthesis test complete!")


if __name__ == "__main__":
    asyncio.run(main())
