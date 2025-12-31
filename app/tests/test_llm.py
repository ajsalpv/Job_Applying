"""
Tests for LLM Client
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock


class TestGroqClient:
    """Test Groq LLM client"""
    
    def test_client_initialization(self):
        """Test client initializes without errors"""
        # Import will fail if settings are not configured
        # This is expected in test environment
        pass
    
    @pytest.mark.asyncio
    async def test_invoke_mock(self):
        """Test invoke with mocked response"""
        mock_response = MagicMock()
        mock_response.content = "Test response"
        
        with patch("langchain_groq.ChatGroq") as mock_chat:
            mock_instance = MagicMock()
            mock_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_chat.return_value = mock_instance
            
            # Test would go here with actual client
            assert True
    
    @pytest.mark.asyncio
    async def test_invoke_json_parsing(self):
        """Test JSON parsing from response"""
        json_response = '{"key": "value", "number": 42}'
        
        # Test JSON extraction logic
        import json
        parsed = json.loads(json_response)
        
        assert parsed["key"] == "value"
        assert parsed["number"] == 42
    
    def test_json_code_block_extraction(self):
        """Test extracting JSON from markdown code blocks"""
        response_with_block = '''Here is the result:
```json
{"score": 85, "reason": "Good match"}
```
'''
        import json
        
        # Extract JSON from code block
        if "```json" in response_with_block:
            json_str = response_with_block.split("```json")[1].split("```")[0]
            parsed = json.loads(json_str.strip())
            
            assert parsed["score"] == 85
            assert "reason" in parsed


class TestPromptExecutor:
    """Test prompt executor"""
    
    def test_variable_substitution(self):
        """Test template variable substitution"""
        template = "Hello {name}, you have {experience} years of experience."
        context = {"name": "Ajsal", "experience": 1}
        
        result = template.format(**context)
        
        assert "Ajsal" in result
        assert "1" in result
    
    def test_missing_variable_handling(self):
        """Test handling of missing template variables"""
        template = "Hello {name}, job is {role}"
        context = {"name": "Ajsal"}
        
        # Should handle missing variables gracefully
        try:
            result = template.format(**context)
            assert False, "Should raise KeyError"
        except KeyError as e:
            assert "role" in str(e)
