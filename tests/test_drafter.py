"""Tests for EssayDrafter."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

from src.drafter import EssayDrafter
from src.models.base import AIModel

class MockAsyncModel(AIModel):
    """Mock model with async support."""
    def __init__(self, model_id, delay=0.1):
        super().__init__(model_id)
        self.delay = delay
        self.call_count = 0

    def call(self, prompt):
        return True, "Sync response", ""

    async def acall(self, prompt):
        self.call_count += 1
        await asyncio.sleep(self.delay)
        return True, f"Draft from {self.model_id}", ""

@pytest.mark.asyncio
async def test_draft_essay_parallel_execution(tmp_path):
    """Test that models run in parallel."""
    model1 = MockAsyncModel("model1", delay=0.2)
    model2 = MockAsyncModel("model2", delay=0.2)
    
    drafter = EssayDrafter([model1, model2])
    
    start_time = asyncio.get_event_loop().time()
    results = await drafter.draft_essay("Test Topic", tmp_path)
    end_time = asyncio.get_event_loop().time()
    
    duration = end_time - start_time
    
    # Both models take 0.2s. If parallel, total time should be ~0.2s, not 0.4s.
    # Allow some overhead, but it should be significantly less than sum.
    assert duration < 0.35
    assert len(results) == 2
    assert results[0]["success"] is True
    assert results[1]["success"] is True
    
    # Verify files created
    assert (tmp_path / "model1.txt").exists()
    assert (tmp_path / "model2.txt").exists()
    assert (tmp_path / "model1.txt").read_text() == "Draft from model1"

@pytest.mark.asyncio
async def test_draft_essay_failure_handling(tmp_path):
    """Test handling of model failures."""
    model1 = MockAsyncModel("model1")
    model2 = MockAsyncModel("model2")

    # Mock model2 to fail
    model2.acall = AsyncMock(return_value=(False, "", "API Error"))

    drafter = EssayDrafter([model1, model2])
    results = await drafter.draft_essay("Test Topic", tmp_path)

    assert len(results) == 2

    # Find results by model
    res1 = next(r for r in results if r["model"] == "model1")
    res2 = next(r for r in results if r["model"] == "model2")

    assert res1["success"] is True
    assert res1["file"] is not None

    assert res2["success"] is False
    assert res2["error"] == "API Error"
    assert res2["file"] is None

@pytest.mark.asyncio
async def test_draft_essay_empty_models(tmp_path):
    """Test handling of empty model list."""
    drafter = EssayDrafter([])
    results = await drafter.draft_essay("Test Topic", tmp_path)

    assert results == []

@pytest.mark.asyncio
async def test_draft_essay_word_count(tmp_path):
    """Test that word count is tracked correctly."""
    model = MockAsyncModel("test-model")

    # Override acall to return a known response
    async def custom_acall(prompt):
        return True, "This is a test essay with exactly ten words here.", ""

    model.acall = custom_acall

    drafter = EssayDrafter([model])
    results = await drafter.draft_essay("Test Topic", tmp_path)

    assert len(results) == 1
    assert results[0]["success"] is True
    assert results[0]["word_count"] == 10

@pytest.mark.asyncio
async def test_draft_essay_model_name_sanitization(tmp_path):
    """Test that model names with special chars are sanitized for filenames."""
    model = MockAsyncModel("anthropic/claude-3:sonnet")

    drafter = EssayDrafter([model])
    results = await drafter.draft_essay("Test Topic", tmp_path)

    assert len(results) == 1
    assert results[0]["success"] is True

    # Check that file was created with sanitized name
    expected_file = tmp_path / "anthropic_claude-3_sonnet.txt"
    assert expected_file.exists()

@pytest.mark.asyncio
async def test_draft_essay_file_write_error(tmp_path):
    """Test handling of file write errors."""
    model = MockAsyncModel("test-model")

    drafter = EssayDrafter([model])

    # Create a read-only directory
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o444)  # Read-only

    try:
        results = await drafter.draft_essay("Test Topic", readonly_dir)

        # The result should indicate failure
        assert len(results) == 1
        assert results[0]["success"] is False
        assert "Failed to save file" in results[0]["error"]
    finally:
        # Cleanup: restore permissions
        readonly_dir.chmod(0o755)
