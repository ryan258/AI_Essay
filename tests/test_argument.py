"""Tests for Argument Analyzer."""

import pytest
from unittest.mock import MagicMock
from src.argument import ArgumentAnalyzer, ArgumentAnalysis, Claim, Fallacy
from src.models.base import AIModel


class MockAIModel(AIModel):
    """Mock AI model for testing."""

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_count = 0

    def call(self, prompt: str):
        self.call_count += 1
        for key, response in self.responses.items():
            if key in prompt:
                return True, response, None
        return True, "", None

    async def acall(self, prompt: str):
        """Async version of call."""
        return self.call(prompt)


@pytest.fixture
def mock_model():
    return MockAIModel()


def test_initialization():
    """Test initialization of ArgumentAnalyzer."""
    analyzer = ArgumentAnalyzer()
    assert analyzer.model is None

    model = MockAIModel()
    analyzer = ArgumentAnalyzer(model=model)
    assert analyzer.model == model


def test_analyze_no_model():
    """Test analysis without a model."""
    analyzer = ArgumentAnalyzer()
    analysis = analyzer.analyze("Some text")
    
    assert analysis.thesis is None
    assert "AI model required" in analysis.critique


def test_parse_structure_response():
    """Test parsing of structure response."""
    analyzer = ArgumentAnalyzer()
    
    response = """
Thesis: AI is beneficial.

Claim 1: It saves time.
Type: supporting
Strength: strong
Evidence: Studies show 50% reduction.
Explanation: Clear evidence provided.

Claim 2: It costs jobs.
Type: counter
Strength: moderate
Evidence: None
Explanation: Valid concern but lacks data.
    """
    
    result = analyzer._parse_structure_response(response)
    
    assert result["thesis"] == "AI is beneficial."
    assert len(result["claims"]) == 2
    
    claim1 = result["claims"][0]
    assert claim1.text == "It saves time."
    assert claim1.type == "supporting"
    assert claim1.strength == "strong"
    
    claim2 = result["claims"][1]
    assert claim2.text == "It costs jobs."
    assert claim2.type == "counter"


def test_parse_fallacy_response():
    """Test parsing of fallacy response."""
    analyzer = ArgumentAnalyzer()
    
    response = """
Fallacy: Ad Hominem
Text: You are wrong because you are silly.
Explanation: Attacking the person not the argument.

Fallacy: Straw Man
Text: They want to ban all cars.
Explanation: Misrepresenting the opponent's view.
    """
    
    fallacies = analyzer._parse_fallacy_response(response)
    
    assert len(fallacies) == 2
    assert fallacies[0].name == "Ad Hominem"
    assert fallacies[0].text == "You are wrong because you are silly."
    assert fallacies[1].name == "Straw Man"


def test_parse_evaluation_response():
    """Test parsing of evaluation response."""
    analyzer = ArgumentAnalyzer()
    
    response = """
Score: 8.5/10
Critique: Good argument but needs more evidence.
Suggestions:
1. Add more citations.
2. Clarify the second point.
3. Address counterarguments.
    """
    
    evaluation = analyzer._parse_evaluation_response(response)
    
    assert evaluation["score"] == 8.5
    assert "Good argument" in evaluation["critique"]
    assert len(evaluation["suggestions"]) == 3
    assert evaluation["suggestions"][0] == "Add more citations."


def test_full_analysis_flow():
    """Test the full analyze method with mocked responses."""
    responses = {
        "Analyze the argument structure": """
Thesis: Testing is good.
Claim 1: It finds bugs.
Type: supporting
Strength: strong
Evidence: None
Explanation: Self-evident.
""",
        "Identify any logical fallacies": "No fallacies found.",
        "Evaluate the overall strength": """
Score: 9/10
Critique: Excellent.
Suggestions:
1. Keep it up.
"""
    }
    
    model = MockAIModel(responses)
    analyzer = ArgumentAnalyzer(model=model)
    
    analysis = analyzer.analyze("Testing is good because it finds bugs.")
    
    assert analysis.thesis == "Testing is good."
    assert len(analysis.claims) == 1
    assert len(analysis.fallacies) == 0
    assert analysis.overall_strength == 9.0
    assert len(analysis.suggestions) == 1


def test_fallacy_detection_found():
    """Test fallacy detection when fallacies are present."""
    responses = {
        "Identify any logical fallacies": """
Fallacy: Circular Reasoning
Text: It is true because I say so.
Explanation: Circular.
"""
    }
    
    model = MockAIModel(responses)
    analyzer = ArgumentAnalyzer(model=model)
    
    # We only care about _detect_fallacies here, but calling analyze triggers it
    # We need to mock other calls to avoid errors or empty results if we want a full run
    # But let's just test the private method directly for specific logic
    fallacies = analyzer._detect_fallacies("It is true because I say so.")
    
    assert len(fallacies) == 1
    assert fallacies[0].name == "Circular Reasoning"
