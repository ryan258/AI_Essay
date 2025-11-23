"""Tests for Phase 3 completion features."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.citations import CitationManager
from src.research import ResearchAssistant

@pytest.fixture
def mock_model():
    model = Mock()
    return model

def test_csl_files_exist():
    """Verify that the required CSL files have been downloaded."""
    styles_dir = Path("styles")
    assert (styles_dir / "mla.csl").exists()
    assert (styles_dir / "chicago-author-date.csl").exists()
    assert (styles_dir / "ieee.csl").exists()

def test_check_plagiarism(mock_model):
    """Test plagiarism detection."""
    mock_model.call.return_value = (True, "Uncited quote 1\nUncited quote 2", "")
    manager = CitationManager(model=mock_model)
    
    issues = manager.check_plagiarism("Some text with quotes.")
    assert len(issues) == 2
    assert issues[0] == "Uncited quote 1"

def test_fact_check(mock_model):
    """Test fact checking."""
    mock_model.call.return_value = (True, '{"supported": true, "confidence": 0.9, "explanation": "Supported by source 1"}', "")
    assistant = ResearchAssistant(model=mock_model)
    
    sources = [{"title": "Source 1", "abstract": "Content supporting claim."}]
    result = assistant.fact_check("Claim", sources)
    
    assert result["supported"] is True
    assert result["confidence"] == 0.9

def test_summarize_source(mock_model):
    """Test source summarization."""
    mock_model.call.return_value = (True, "This is a summary.", "")
    assistant = ResearchAssistant(model=mock_model)
    
    source = {"title": "Paper", "abstract": "Long abstract..."}
    summary = assistant.summarize_source(source)
    
    assert summary == "This is a summary."
