
from src.argument import ArgumentAnalyzer
def test_malformed_structure_response():
    """Test handling of malformed structure response."""
    analyzer = ArgumentAnalyzer()
    
    # Missing required fields
    response = """
Thesis: Some thesis
Claim 1: Broken claim
Type: supporting
    """
    
    result = analyzer._parse_structure_response(response)
    
    # Should keep the claim with defaults
    assert result["thesis"] == "Some thesis"
    assert len(result["claims"]) == 1
    assert result["claims"][0].strength == "moderate"  # Default value


def test_malformed_fallacy_response():
    """Test handling of malformed fallacy response."""
    analyzer = ArgumentAnalyzer()
    
    # Missing explanation
    response = """
Fallacy: Bad Logic
Text: Some text
    """
    
    fallacies = analyzer._parse_fallacy_response(response)
    
    # Should keep fallacy with defaults
    assert len(fallacies) == 1
    assert fallacies[0].explanation == ""  # Default value


def test_malformed_score_response():
    """Test handling of malformed score response."""
    analyzer = ArgumentAnalyzer()
    
    response = """
Score: Not a number
Critique: Good
    """
    
    evaluation = analyzer._parse_evaluation_response(response)
    
    assert evaluation["score"] == 0.0
    assert evaluation["critique"] == "Good"


def test_empty_input_validation():
    """Test validation of empty input."""
    analyzer = ArgumentAnalyzer()
    
    analysis = analyzer.analyze("")
    
    assert analysis.thesis is None
    assert "No text provided" in analysis.critique
