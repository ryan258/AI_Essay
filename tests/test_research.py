"""Tests for ResearchAssistant."""

import pytest
from unittest.mock import Mock, patch
from src.research import ResearchAssistant

@pytest.fixture
def mock_model():
    model = Mock()
    model.call.return_value = (True, "query1\nquery2", "")
    return model

@pytest.fixture
def assistant(mock_model):
    return ResearchAssistant(model=mock_model)

def test_search_papers_success(assistant):
    with patch.object(assistant.sch, 'search_paper') as mock_search:
        mock_item = Mock()
        mock_item.title = "Test Paper"
        mock_item.url = "http://test.com"
        mock_item.abstract = "Abstract"
        mock_item.year = 2023
        mock_item.authors = [Mock(name="Author")]
        mock_item.citationCount = 10
        mock_item.paperId = "123"
        
        mock_search.return_value = [mock_item]
        
        results = assistant.search_papers("query", limit=1)
        
        assert len(results) == 1
        assert results[0]['title'] == "Test Paper"
        assert results[0]['paperId'] == "123"

def test_suggest_sources_fallback(assistant):
    # Test fallback when model is None
    assistant.model = None
    with patch.object(assistant, 'search_papers') as mock_search:
        mock_search.return_value = [{"title": "Fallback Paper", "paperId": "1"}]
        
        results = assistant.suggest_sources("This is an essay about AI.", limit=1)
        
        assert len(results) == 1
        assert results[0]['title'] == "Fallback Paper"
        # Verify fallback query logic (first 5 words)
        mock_search.assert_called_with("This is an essay about", limit=1)
