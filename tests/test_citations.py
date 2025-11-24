"""Tests for CitationManager."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.citations import CitationManager
from src.exceptions import CitationError

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
    """Test error handling for unsupported style."""
    manager.add_source({"title": "Test Source", "author": [{"family": "Doe", "given": "John"}], "issued": {"date-parts": [[2023]]}, "type": "article-journal"})
    
    # Test with non-existent style
    with pytest.raises(CitationError):
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
    source = manager._best_source_for_claim(claim, lenient=True)
    assert source["id"] == "1"


def test_best_source_for_claim_no_match_strict_returns_none(manager):
    manager.add_source({"id": "1", "title": "Quantum Physics", "abstract": ""})
    claim = "Economics theory suggests"
    source = manager._best_source_for_claim(claim, lenient=False)
    assert source is None


def test_cite_no_sources_auto_insert_does_not_write(tmp_path, monkeypatch):
    """When no sources exist and auto_insert=True, cite should not write output if nothing changes."""
    essay_file = tmp_path / "essay.txt"
    essay_file.write_text("This is a claim without sources.")

    # Patch CitationManager to avoid AI calls
    with patch("src.essay.CitationManager") as mock_manager_cls:
        mock_manager = Mock()
        mock_manager.find_claims.return_value = ["This is a claim without sources."]
        mock_manager.sources = []
        mock_manager.generate_bibliography.return_value = ""
        mock_manager.format_citation.return_value = "(X)"
        mock_manager_cls.return_value = mock_manager

        from src.essay import EssayCLI

        cli = EssayCLI()
        cli.cite(str(essay_file), auto_insert=True, annotate_missing=False, generate_bibliography=False, model=None)

    cited_file = essay_file.with_name("essay_cited.txt")
    assert not cited_file.exists()
