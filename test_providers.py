#!/usr/bin/env python3
"""
Test script to show LLM provider/model pairs
"""
import sys
import os
sys.path.insert(0, 'backend')

# Test each provider by temporarily setting the environment variable
providers = {
    'openai': 'GPT-4o (best available - GPT-5 Nano doesn\'t exist yet)',
    'claude': 'Claude 3.5 Haiku',
    'gemini': 'Gemini 2.5 Flash-Lite', 
    'lmstudio': 'openai/gpt-oss-20b',
    'ollama': 'openai/gpt-oss-20b'
}

print("🤖 Your Preferred LLM Provider/Model Pairs")
print("=" * 50)

for provider, description in providers.items():
    # Set the provider via environment
    os.environ['LLM_PROVIDER'] = provider
    
    # Reload settings
    from packages.shared.config import Settings
    settings = Settings()
    
    print("12")

print()
print("💡 To switch providers, just change LLM_PROVIDER in your .env file!")
print("   The system will automatically use the correct model for each provider.")
