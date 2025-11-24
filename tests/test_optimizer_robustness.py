
import pytest
from src.optimizer import GrammarOptimizer

def test_malformed_ai_grammar_response():
    """Test handling of malformed AI grammar response."""
    optimizer = GrammarOptimizer()
    
    # Missing description
    response = """
Type: grammar
Original: bad
Suggestion: good
    """
    
    issues = optimizer._parse_ai_grammar_response(response)
    
    # Should skip incomplete issue
    assert len(issues) == 0


def test_optimizer_empty_input():
    """Test optimizer with empty input."""
    optimizer = GrammarOptimizer()
    
    result = optimizer.optimize("")
    
    assert len(result.issues) == 0
    assert result.metrics.total_words == 0
