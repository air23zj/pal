#!/usr/bin/env python3
"""
PAL API Keys Testing Script
Tests all configured API keys to verify they are working correctly.
"""
import os
import sys
import asyncio
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    from packages.shared.config import settings
    from packages.connectors.research import ResearchConnector
    from packages.connectors.news import NewsConnector
    from packages.connectors.flights import FlightsConnector
    from packages.connectors.dining import DiningConnector
    from packages.connectors.travel import TravelConnector
    from packages.connectors.local import LocalConnector
    from packages.connectors.shopping import ShoppingConnector
    from packages.connectors.keep import KeepConnector
    from packages.connectors.gmail import GmailConnector
    from packages.connectors.calendar import CalendarConnector
    from packages.connectors.tasks import TasksConnector
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


class APIKeyTester:
    """Test all configured API keys and integrations."""

    def __init__(self):
        self.results = []
        self.start_time = datetime.now(timezone.utc)

    def log_result(self, api_name: str, status: str, message: str = "", error: Optional[str] = None):
        """Log a test result."""
        result = {
            'api': api_name,
            'status': status,
            'message': message,
            'error': error,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.results.append(result)

        # Print to console
        status_icon = "✅" if status == "success" else "❌" if status == "failed" else "⚠️"
        print(f"{status_icon} {api_name}: {message}")
        if error:
            print(f"   Error: {error}")

    async def test_openai_key(self):
        """Test OpenAI API key."""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

            # Simple test - get models list
            response = await client.models.list()
            if response.data:
                self.log_result("OpenAI", "success", f"API key valid, {len(response.data)} models available")
            else:
                self.log_result("OpenAI", "failed", "API key valid but no models returned")
        except Exception as e:
            if "api_key" in str(e).lower() or "invalid" in str(e).lower():
                self.log_result("OpenAI", "failed", "Invalid API key", str(e))
            else:
                self.log_result("OpenAI", "failed", "Connection error", str(e))

    async def test_anthropic_key(self):
        """Test Anthropic/Claude API key."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

            # Simple test - list models or basic API call
            # Note: Anthropic doesn't have a models list endpoint like OpenAI
            # We'll do a minimal completion test
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            if response.content:
                self.log_result("Anthropic", "success", "API key valid, Claude accessible")
            else:
                self.log_result("Anthropic", "warning", "API key valid but unexpected response")
        except Exception as e:
            if "api_key" in str(e).lower() or "invalid" in str(e).lower():
                self.log_result("Anthropic", "failed", "Invalid API key", str(e))
            else:
                self.log_result("Anthropic", "failed", "Connection error", str(e))

    async def test_serpapi_key(self):
        """Test SerpApi key."""
        if not settings.serpapi_api_key:
            self.log_result("SerpApi", "failed", "No API key configured")
            return

        try:
            # Use the ResearchConnector which uses SerpApi
            connector = ResearchConnector(api_key=settings.serpapi_api_key)
            if not connector.is_available():
                self.log_result("SerpApi", "failed", "Connector reports unavailable")
                return

            # Try a simple search
            result = await connector.fetch(since=None, limit=1)
            if result.status == "ok" and result.items:
                self.log_result("SerpApi", "success", f"API key valid, returned {len(result.items)} result(s)")
            elif result.status == "ok" and not result.items:
                self.log_result("SerpApi", "warning", "API key valid but no results returned")
            else:
                self.log_result("SerpApi", "failed", f"API error: {result.error_message}")
        except Exception as e:
            self.log_result("SerpApi", "failed", "Connection error", str(e))

    async def test_serper_key(self):
        """Test Serper search API key."""
        if not settings.serper_search_api_key:
            self.log_result("Serper", "failed", "No API key configured")
            return

        try:
            # Test direct API call to Serper
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "q": "test query",
                    "num": 1
                }
                headers = {
                    "X-API-KEY": settings.serper_search_api_key,
                    "Content-Type": "application/json"
                }

                async with session.post(
                    "https://google.serper.dev/search",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "organic" in data:
                            self.log_result("Serper", "success", "API key valid")
                        else:
                            self.log_result("Serper", "warning", "API key valid but unexpected response format")
                    else:
                        error_text = await response.text()
                        self.log_result("Serper", "failed", f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("Serper", "failed", "Connection error", str(e))

    async def test_newsapi_key(self):
        """Test News API key."""
        if not settings.news_api_key:
            self.log_result("NewsAPI", "failed", "No API key configured")
            return

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                params = {
                    "apiKey": settings.news_api_key,
                    "q": "test",
                    "pageSize": 1
                }

                async with session.get(
                    "https://newsapi.org/v2/everything",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "articles" in data:
                            self.log_result("NewsAPI", "success", f"API key valid, found {len(data.get('articles', []))} articles")
                        else:
                            self.log_result("NewsAPI", "warning", "API key valid but unexpected response format")
                    else:
                        error_text = await response.text()
                        self.log_result("NewsAPI", "failed", f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("NewsAPI", "failed", "Connection error", str(e))


    async def test_gemini_key(self):
        """Test Google Gemini API key."""
        if not settings.gemini_api_key:
            self.log_result("Gemini", "failed", "No API key configured")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)

            # Test with a simple model (gemini-pro should work)
            try:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content("Hello world")
                if response and hasattr(response, 'text') and response.text:
                    self.log_result("Gemini", "success", "API key valid, Gemini accessible")
                else:
                    self.log_result("Gemini", "warning", "API key valid but unexpected response format")
            except Exception as e:
                error_str = str(e)
                if "API_KEY" in error_str.upper() or "invalid" in error_str.lower():
                    self.log_result("Gemini", "failed", "Invalid API key", error_str)
                elif "model" in error_str.lower() and "not found" in error_str.lower():
                    self.log_result("Gemini", "failed", "Model not available", error_str)
                else:
                    self.log_result("Gemini", "failed", "Connection or configuration error", error_str)
            if response.text:
                self.log_result("Gemini", "success", "API key valid, Gemini accessible")
            else:
                self.log_result("Gemini", "warning", "API key valid but empty response")
        except Exception as e:
            if "api_key" in str(e).lower() or "invalid" in str(e).lower():
                self.log_result("Gemini", "failed", "Invalid API key", str(e))
            else:
                self.log_result("Gemini", "failed", "Connection error", str(e))

    async def test_openweather_key(self):
        """Test OpenWeatherMap API key."""
        if not settings.openweather_api_key:
            self.log_result("OpenWeatherMap", "failed", "No API key configured")
            return

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": "London",
                    "appid": settings.openweather_api_key,
                    "units": "metric"
                }

                async with session.get(
                    "http://api.openweathermap.org/data/2.5/weather",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "main" in data and "temp" in data["main"]:
                            temp = data["main"]["temp"]
                            self.log_result("OpenWeatherMap", "success", f"API key valid, London temp: {temp}°C")
                        else:
                            self.log_result("OpenWeatherMap", "warning", "API key valid but unexpected response format")
                    else:
                        error_text = await response.text()
                        self.log_result("OpenWeatherMap", "failed", f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("OpenWeatherMap", "failed", "Connection error", str(e))

    async def test_google_services(self):
        """Test Google Workspace services (OAuth-based)."""
        services = [
            ("Gmail", GmailConnector()),
            ("Calendar", CalendarConnector()),
            ("Tasks", TasksConnector()),
            ("Keep", KeepConnector()),
        ]

        for service_name, connector in services:
            try:
                available = connector.is_available()
                if available:
                    # Try to connect (this will test OAuth tokens)
                    connected = await connector.connect()
                    if connected:
                        self.log_result(f"Google {service_name}", "success", "Credentials valid and OAuth working")
                        # Clean up connection
                        if hasattr(connector, '_service'):
                            connector._service = None
                    else:
                        self.log_result(f"Google {service_name}", "failed", "OAuth authentication failed")
                else:
                    self.log_result(f"Google {service_name}", "failed", "Credentials file not found")
            except Exception as e:
                self.log_result(f"Google {service_name}", "failed", "Connection error", str(e))

    async def test_connector_apis(self):
        """Test connector-based APIs that use SerpApi."""
        connectors = [
            ("News", NewsConnector(api_key=settings.serpapi_api_key)),
            ("Flights", FlightsConnector(api_key=settings.serpapi_api_key)),
            ("Dining", DiningConnector(api_key=settings.serpapi_api_key)),
            ("Travel", TravelConnector(api_key=settings.serpapi_api_key)),
            ("Local", LocalConnector(api_key=settings.serpapi_api_key)),
            ("Shopping", ShoppingConnector(api_key=settings.serpapi_api_key)),
        ]

        for name, connector in connectors:
            try:
                if connector.is_available():
                    # Try a minimal fetch
                    result = await connector.fetch(since=None, limit=1)
                    if result.status == "ok":
                        items_count = len(result.items)
                        self.log_result(f"{name} Connector", "success", f"API working, returned {items_count} item(s)")
                    else:
                        self.log_result(f"{name} Connector", "failed", f"API error: {result.error_message}")
                else:
                    self.log_result(f"{name} Connector", "failed", "SerpApi key not configured or connector unavailable")
            except Exception as e:
                self.log_result(f"{name} Connector", "failed", "Connection error", str(e))

    async def run_all_tests(self):
        """Run all API key tests."""
        print("🔍 PAL API Keys Testing")
        print("=" * 50)

        # LLM APIs
        print("\n🤖 LLM APIs:")
        await self.test_openai_key()
        await self.test_anthropic_key()
        await self.test_gemini_key()

        # Search APIs
        print("\n🔍 Search APIs:")
        await self.test_serpapi_key()
        await self.test_serper_key()

        # Other APIs
        print("\n📡 Other APIs:")
        await self.test_newsapi_key()
        await self.test_openweather_key()

        # Google Services
        print("\n📧 Google Workspace Services:")
        await self.test_google_services()

        # Connector APIs
        print("\n🔗 Connector APIs:")
        await self.test_connector_apis()

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)

        successful = len([r for r in self.results if r['status'] == 'success'])
        failed = len([r for r in self.results if r['status'] == 'failed'])
        warnings = len([r for r in self.results if r['status'] == 'warning'])
        total = len(self.results)

        print(f"Total tests: {total}")
        print(f"✅ Successful: {successful}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"❌ Failed: {failed}")

        duration = datetime.now(timezone.utc) - self.start_time
        print(f"Duration: {duration.total_seconds():.2f} seconds")

        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if result['status'] == 'failed':
                    print(f"  • {result['api']}: {result['message']}")
                    if result['error']:
                        print(f"    Error: {result['error']}")

        if warnings > 0:
            print("\n⚠️  WARNINGS:")
            for result in self.results:
                if result['status'] == 'warning':
                    print(f"  • {result['api']}: {result['message']}")

        print("\n✅ WORKING APIs:")
        working_apis = [r['api'] for r in self.results if r['status'] == 'success']
        if working_apis:
            for api in working_apis:
                print(f"  • {api}")
        else:
            print("  None found")


async def main():
    """Main entry point."""
    tester = APIKeyTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())