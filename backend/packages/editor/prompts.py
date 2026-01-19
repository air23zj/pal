"""
Prompt templates for brief synthesis
"""

SYSTEM_PROMPT = """You are an AI assistant helping to create personalized morning briefings.
Your task is to explain why items are important and create concise summaries.

Guidelines:
- Be concise and clear (1-2 sentences max)
- Focus on personal relevance and impact
- Use second person ("you", "your")
- Be specific and actionable
- Maintain professional tone"""


WHY_IT_MATTERS_PROMPT = """Given this item from a morning brief, explain in 1-2 sentences why it matters to the user.

Item Details:
- Title: {title}
- Summary: {summary}
- Source: {source}
- Type: {type}
- Timestamp: {timestamp}

Context:
- User's topics of interest: {user_topics}
- VIP people: {vip_people}
- Important projects: {projects}

Relevance Score: {relevance_score:.2f}
Urgency Score: {urgency_score:.2f}

Explain why this matters to the user. Focus on:
1. How it relates to their interests or responsibilities
2. What action might be needed
3. Potential impact or consequences

"Why it matters" explanation:"""


MODULE_SUMMARY_PROMPT = """Create a brief one-sentence summary for this module in a morning brief.

Module: {module_name}
Items ({item_count}):
{items_summary}

Key stats:
- New items: {new_count}
- Updated items: {updated_count}
- Urgent items: {urgent_count}

Create a concise summary that:
1. States the count and what's notable
2. Highlights any urgent or important items
3. Gives quick actionable insight

One-sentence summary:"""


BRIEF_OVERVIEW_PROMPT = """Create a personalized greeting and overview for this morning brief.

User: {user_name}
Date: {date}
Time generated: {time}
Timezone: {timezone}

Highlights:
{highlights_summary}

Total items: {total_items}
Modules with updates: {modules_with_updates}

Create a warm, concise greeting (2-3 sentences) that:
1. Greets the user
2. Summarizes what's in this brief
3. Calls out any urgent items

Greeting and overview:"""


COMPRESS_SUMMARY_PROMPT = """Compress this summary to be more concise while keeping key information.

Original summary:
{summary}

Create a compressed version (max 100 characters) that preserves the most important information:"""
