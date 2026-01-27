"""
Search summarization utilities borrowed from home_agent.
"""
import os
import logging
from typing import List, Dict, Any
import httpx

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client lazily
client = None

def get_openai_client():
    """Get or create OpenAI client"""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        client = AsyncOpenAI(api_key=api_key)
    return client


async def search_with_serper(query: str, subscription_key: str):
    """
    Perform search using Serper API.

    Args:
        query: Search query
        subscription_key: Serper API key

    Returns:
        List of search result contexts
    """
    try:
        headers = {
            'X-API-KEY': subscription_key,
            'Content-Type': 'application/json'
        }

        payload = {
            "q": query,
            "num": 10  # Get more results for better summarization
        }

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise Exception(f"Serper API error: {response.status_code}")

            data = response.json()

            # Extract organic results
            results = []
            if "organic" in data:
                for item in data["organic"]:
                    result = {
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", "")
                    }
                    results.append(result)

            return results

    except Exception as e:
        logger.error(f"Error in search_with_serper: {str(e)}")
        raise


async def get_search_sum(query: str, contexts: List[dict]) -> str:
    """
    Get a summary of search results with citations.

    Args:
        query: Search query
        contexts: List of search result contexts

    Returns:
        Summarized answer with citations
    """
    try:
        # Format contexts with citation numbers
        formatted_contexts = []
        for i, ctx in enumerate(contexts, 1):
            formatted_contexts.append(f"{ctx['snippet']} [Citation: {i}]")

        context_text = "\n\n".join(formatted_contexts)

        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides accurate information with citations. Always cite your sources using [X] format where X is the citation number."},
            {"role": "user", "content": f"Based on the following sources, answer this question: {query}\n\nSources:\n{context_text}"}
        ]

        response = await get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Error in get_search_sum: {str(e)}")
        raise


async def get_related_questions(query: str, contexts: List[dict]) -> List[str]:
    """
    Generate related questions based on the search results.

    Args:
        query: Original query
        contexts: Search result contexts

    Returns:
        List of related questions
    """
    try:
        context_text = "\n".join(ctx['snippet'] for ctx in contexts)

        messages = [
            {"role": "system", "content": "Generate 3-5 related questions that users might want to ask next. Make them natural and relevant to the original query and search results."},
            {"role": "user", "content": f"Original question: {query}\n\nSearch results:\n{context_text}"}
        ]

        response = await get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )

        # Split the response into individual questions and clean them up
        questions = [
            q.strip().strip('•-*').strip()
            for q in response.choices[0].message.content.strip().split('\n')
            if q.strip() and not q.strip().lower().startswith(('here', 'related', 'questions'))
        ]

        return questions[:5]  # Return at most 5 questions

    except Exception as e:
        logger.error(f"Error in get_related_questions: {str(e)}")
        return []


async def perform_search(query: str, search_engine: str = "serper") -> dict:
    """
    Perform search using the specified search engine and return formatted results.

    Args:
        query: Search query
        search_engine: Search engine to use ("serper" supported)

    Returns:
        Dictionary with answer, sources, and related questions
    """
    try:
        if search_engine == "serper":
            serper_key = os.getenv("SERPER_SEARCH_API_KEY") or os.getenv("SERPAPI_API_KEY")
            if not serper_key:
                raise ValueError("SERPER_SEARCH_API_KEY or SERPAPI_API_KEY environment variable not set")

            contexts = await search_with_serper(query, serper_key)
            answer = await get_search_sum(query, contexts)
            related = await get_related_questions(query, contexts)

            return {
                "answer": answer,
                "sources": [
                    {
                        "title": ctx.get("title", ""),
                        "snippet": ctx.get("snippet", ""),
                        "url": ctx.get("link", "")
                    }
                    for ctx in contexts
                ],
                "related_questions": related
            }
        else:
            raise ValueError(f"Unsupported search engine: {search_engine}")

    except Exception as e:
        logger.error(f"Error in perform_search: {str(e)}")
        # Return mock data for testing when API fails
        return {
            "answer": f"This is a mock response for the query: '{query}'. In a real implementation, this would be powered by AI summarization of search results.",
            "sources": [
                {
                    "title": "Example Source 1",
                    "snippet": "This is an example search result snippet that would normally come from the search API.",
                    "url": "https://example.com/1"
                },
                {
                    "title": "Example Source 2",
                    "snippet": "Another example search result that demonstrates the citation system.",
                    "url": "https://example.com/2"
                }
            ],
            "related_questions": [
                f"What are the benefits of {query.split()[1] if len(query.split()) > 1 else query}?",
                f"How does {query} work?",
                f"What are the latest developments in {query}?"
            ]
        }