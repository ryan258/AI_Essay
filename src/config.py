"""Configuration settings for the AI Essay project."""

import os
from pathlib import Path
from typing import Dict, Any
import yaml

class Config:
    """Central configuration management."""

    # Default Constants
    DEFAULT_MODEL = "anthropic/claude-3-haiku"
    MAX_ESSAY_LENGTH = 2000
    DEFAULT_SEARCH_LIMIT = 5
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    CONFIG_FILE = PROJECT_ROOT / "config.yaml"

    def __init__(self):
        """Initialize configuration."""
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from yaml file."""
        if not self.CONFIG_FILE.exists():
            return {}
        
        try:
            with open(self.CONFIG_FILE, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    @property
    def default_model(self) -> str:
        """Get default model name."""
        return os.getenv("OPENROUTER_MODEL", self.DEFAULT_MODEL)

    @property
    def max_tokens(self) -> int:
        """Get max tokens."""
        return self._config.get("defaults", {}).get("max_tokens", 1000)

    @property
    def temperature(self) -> float:
        """Get temperature."""
        return self._config.get("defaults", {}).get("temperature", 1.0)

    @property
    def retry_limit(self) -> int:
        """Get retry limit."""
        return self._config.get("defaults", {}).get("retry_limit", self.MAX_RETRIES)

# Global config instance
config = Config()
