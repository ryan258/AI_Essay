"""Tests for OpenRouterModel."""

import os
import pytest
from unittest.mock import Mock, patch
from src.models.openrouter import OpenRouterModel
from src.exceptions import ModelError

@pytest.fixture
def mock_env_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")

def test_init_with_env_key(mock_env_api_key):
    model = OpenRouterModel(model_name="test-model")
    assert model.api_key == "test_key"
    assert model.model_id == "test-model"

def test_init_with_explicit_key():
    model = OpenRouterModel(model_name="test-model", api_key="explicit_key")
    assert model.api_key == "explicit_key"

def test_init_missing_key():
    """Test initialization without API key."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ModelError):
            OpenRouterModel(model_name="test-model", api_key=None)

@patch("src.models.openrouter.OpenAI")
def test_call_success(mock_openai, mock_env_api_key):
    # Setup mock response
    mock_client = Mock()
    mock_completion = Mock()
    mock_message = Mock()
    mock_message.content = "Test response"
    mock_completion.choices = [Mock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_completion
    mock_openai.return_value = mock_client

    model = OpenRouterModel(model_name="test-model")
    success, response, error = model.call("Test prompt")

    assert success is True
    assert response == "Test response"
    assert error == ""
    
    # Verify API call arguments
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args[1]
    assert call_args["model"] == "test-model"
    assert call_args["messages"][1]["content"] == "Test prompt"

@patch("src.models.openrouter.OpenAI")
def test_call_failure(mock_openai, mock_env_api_key):
    # Setup mock to raise exception
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    mock_openai.return_value = mock_client

    model = OpenRouterModel(model_name="test-model")
    success, response, error = model.call("Test prompt")

    assert success is False
    assert response == ""
    assert "API Error" in error

def test_repr(mock_env_api_key):
    model = OpenRouterModel(model_name="test-model", max_tokens=500, temperature=0.7)
    repr_str = repr(model)
    assert "test-model" in repr_str
    assert "500" in repr_str
    assert "0.7" in repr_str
