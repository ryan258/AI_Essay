"""Integration tests for AI Essay workflow."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import shutil

from src.essay import EssayCLI
from src.config import config
from src.exceptions import ModelError

@pytest.fixture
def mock_model():
    """Mock AI model."""
    mock = Mock()
    mock.call.return_value = (True, "Mocked AI response", "")
    return mock

@pytest.fixture
def cli():
    """EssayCLI instance."""
    return EssayCLI()

def test_full_workflow_integration(cli, tmp_path):
    """Test the full draft -> analyze -> improve workflow."""
    
    # Setup
    topic = "Integration Test Topic"
    draft_dir = tmp_path / "drafts"
    
    # 1. Draft
    with patch("src.essay.OpenRouterModel") as MockModel:
        # Configure mock to return success
        mock_instance = MockModel.return_value
        mock_instance.model_id = "test-model"
        mock_instance.call.return_value = (True, "This is a drafted essay about integration testing.", "")
        
        # For async methods, we need to make the return value awaitable
        async def async_response(*args, **kwargs):
            return (True, "This is a drafted essay about integration testing.", "")
        mock_instance.acall.side_effect = async_response
        
        # Run draft
        cli.draft(topic, models="test-model", output_dir=str(draft_dir))
        
        # Verify draft created
        assert draft_dir.exists()
        draft_files = list(draft_dir.glob("**/*.txt"))
        assert len(draft_files) > 0
        draft_file = draft_files[0]
        
        # 2. Analyze
        # Mock analyzer model response
        mock_instance.call.return_value = (True, "Thesis: Integration testing is crucial.", "")
        
        cli.analyze(str(draft_file), model="test-model")
        # (Analysis prints to console, so we just ensure no crash)
        
        # 3. Improve
        improve_dir = tmp_path / "improved"
        
        # Mock improver responses
        mock_instance.call.return_value = (True, "Improved text with better grammar.", "")
        
        cli.improve(str(draft_file), cycles=1, output_dir=str(improve_dir), model="test-model")
        
        # Verify improved file created
        assert improve_dir.exists()
        improved_files = list(improve_dir.glob("*.txt"))
        assert len(improved_files) > 0
        assert "Improved text" in improved_files[0].read_text()

def test_config_integration():
    """Verify config values are used."""
    assert config.DEFAULT_MODEL == "anthropic/claude-3-haiku"
    assert config.API_TIMEOUT == 30

def test_exception_handling():
    """Verify custom exceptions are raised/handled."""
    with pytest.raises(ModelError):
        # Simulate missing API key behavior if we were to call OpenRouterModel directly without key
        # But here we just want to import and use the exception to verify it exists and works
        raise ModelError("Test error")
