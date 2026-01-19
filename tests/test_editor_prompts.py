"""
Tests for editor prompts module
"""
import pytest
from packages.editor.prompts import WHY_IT_MATTERS_PROMPT, MODULE_SUMMARY_PROMPT, SYSTEM_PROMPT


class TestPrompts:
    """Test prompt templates"""
    
    def test_why_it_matters_prompt_exists(self):
        """Test that why_it_matters prompt is defined"""
        assert WHY_IT_MATTERS_PROMPT is not None
        assert isinstance(WHY_IT_MATTERS_PROMPT, str)
        assert len(WHY_IT_MATTERS_PROMPT) > 0
    
    def test_module_summary_prompt_exists(self):
        """Test that module_summary prompt is defined"""
        assert MODULE_SUMMARY_PROMPT is not None
        assert isinstance(MODULE_SUMMARY_PROMPT, str)
        assert len(MODULE_SUMMARY_PROMPT) > 0
    
    def test_system_prompt_exists(self):
        """Test that system prompt is defined"""
        assert SYSTEM_PROMPT is not None
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0
    
    def test_prompts_are_non_empty(self):
        """Test that all prompts have meaningful content"""
        assert len(WHY_IT_MATTERS_PROMPT.strip()) > 50
        assert len(MODULE_SUMMARY_PROMPT.strip()) > 50
        assert len(SYSTEM_PROMPT.strip()) > 50
    
    def test_prompts_contain_instructions(self):
        """Test that prompts contain instruction keywords"""
        # Why it matters should mention item or brief
        assert any(word in WHY_IT_MATTERS_PROMPT.lower() for word in ['item', 'brief', 'explain', 'matter'])
        
        # Module summary should mention module or summary
        assert any(word in MODULE_SUMMARY_PROMPT.lower() for word in ['module', 'summary', 'summarize'])
        
        # System prompt should set context
        assert any(word in SYSTEM_PROMPT.lower() for word in ['assistant', 'help', 'brief', 'system'])
    
    def test_prompts_are_distinct(self):
        """Test that prompts are different from each other"""
        assert WHY_IT_MATTERS_PROMPT != MODULE_SUMMARY_PROMPT
        assert WHY_IT_MATTERS_PROMPT != SYSTEM_PROMPT
        assert MODULE_SUMMARY_PROMPT != SYSTEM_PROMPT
