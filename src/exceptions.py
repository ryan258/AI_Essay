"""Custom exceptions for the AI Essay project."""

class AIError(Exception):
    """Base exception for AI Essay project."""
    pass

class ModelError(AIError):
    """Raised when an AI model fails."""
    pass

class CitationError(AIError):
    """Raised when citation lookup or generation fails."""
    pass

class ResearchError(AIError):
    """Raised when research or source finding fails."""
    pass

class ConfigurationError(AIError):
    """Raised when configuration is invalid."""
    pass
