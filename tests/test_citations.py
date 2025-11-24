"""Tests for CitationManager."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.citations import CitationManager

@pytest.fixture
def mock_model():
    model = Mock()
    model.call.return_value = (True, "Claim 1\nClaim 2", "")
    return model

@pytest.fixture
def manager(mock_model):
    return CitationManager(model=mock_model)

def test_find_claims(manager):
    claims = manager.find_claims("Some text")
    assert len(claims) == 2
    assert claims[0] == "Claim 1"

def test_add_source(manager):
    source = {"title": "Test Source", "type": "article-journal"}
    manager.add_source(source)
    assert len(manager.sources) == 1
    assert manager.sources[0]['id'] == "source-1"

def test_generate_bibliography_missing_style(manager):
    manager.add_source({"id": "1", "title": "Test", "type": "article-journal"})
    
    # Test with non-existent style
    with pytest.raises(ValueError):
        manager.generate_bibliography(style="non_existent_style")

def test_generate_bibliography_valid(manager):
    # Mock file existence for a valid style
    with patch("pathlib.Path.exists", return_value=True):
        # We also need to mock CitationStylesStyle and Bibliography since we don't have real CSL files in test env usually
        with patch("src.citations.CitationStylesStyle") as mock_style, \
             patch("src.citations.CitationStylesBibliography") as mock_bib:

            mock_bib_instance = Mock()
            mock_bib_instance.bibliography.return_value = ["Reference 1"]
            mock_bib.return_value = mock_bib_instance

            manager.add_source({"id": "1", "title": "Test", "type": "article-journal"})
            result = manager.generate_bibliography(style="apa")

            assert "Reference 1" in result


def test_best_source_for_claim_keyword_match(manager):
    manager.add_source({"id": "1", "title": "Machine Learning Study", "abstract": "AI research and models."})
    manager.add_source({"id": "2", "title": "Biology Overview", "abstract": "Cells and DNA."})

    claim = "Machine learning algorithms improve accuracy"
    source = manager._best_source_for_claim(claim)
    assert source["id"] == "1"


def test_best_source_for_claim_no_match_returns_first(manager):
    manager.add_source({"id": "1", "title": "Quantum Physics", "abstract": ""})
    claim = "Economics theory suggests"
    source = manager._best_source_for_claim(claim)
    assert source["id"] == "1"
