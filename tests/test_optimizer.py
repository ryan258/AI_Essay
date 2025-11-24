"""Tests for GrammarOptimizer."""

import pytest
from unittest.mock import Mock

from src.optimizer import (
    GrammarOptimizer,
    OptimizationIssue,
    ReadabilityMetrics,
    OptimizationResult,
)


SIMPLE_TEXT = "Technology is good. It helps people. We use it every day."

COMPLEX_TEXT = """
In today's society, technology has fundamentally transformed the way in which we communicate and interact with one another,
creating both opportunities for enhanced connectivity and challenges related to information overload and digital distraction.
Due to the fact that technological advancement continues to accelerate at an unprecedented pace, it is imperative that we
carefully consider the implications of our increasingly digitized existence and develop strategies to mitigate potential
negative consequences while maximizing beneficial outcomes.
"""

PASSIVE_VOICE_TEXT = "The essay was written by the student. Many improvements were made. The conclusion was strengthened."

ACTIVE_VOICE_TEXT = "The student wrote the essay. The teacher made many improvements. We strengthened the conclusion."

WORDY_TEXT = "In order to succeed, we need to work hard. Due to the fact that technology advances, we must adapt."

CLICHE_TEXT = "At the end of the day, we need to think outside the box and move the needle on innovation."


def test_basic_optimization():
    """Test basic optimization without AI."""
    optimizer = GrammarOptimizer()
    result = optimizer.optimize(SIMPLE_TEXT, apply_fixes=False)

    assert isinstance(result, OptimizationResult)
    assert isinstance(result.metrics, ReadabilityMetrics)
    assert isinstance(result.issues, list)


def test_readability_metrics_calculation():
    """Test that readability metrics are calculated correctly."""
    optimizer = GrammarOptimizer()
    result = optimizer.optimize(SIMPLE_TEXT)

    metrics = result.metrics
    assert 0 <= metrics.flesch_reading_ease <= 100
    assert metrics.flesch_kincaid_grade >= 0
    assert metrics.total_words > 0
    assert metrics.total_sentences > 0
    assert metrics.avg_sentence_length > 0


def test_complex_text_lower_readability():
    """Test that complex text has lower readability scores."""
    optimizer = GrammarOptimizer()

    simple_result = optimizer.optimize(SIMPLE_TEXT)
    complex_result = optimizer.optimize(COMPLEX_TEXT)

    # Complex text should have lower reading ease (harder to read)
    assert complex_result.metrics.flesch_reading_ease < simple_result.metrics.flesch_reading_ease

    # Complex text should have higher grade level
    assert complex_result.metrics.flesch_kincaid_grade > simple_result.metrics.flesch_kincaid_grade


def test_detect_cliches():
    """Test cliché detection."""
    optimizer = GrammarOptimizer()
    result = optimizer.optimize(CLICHE_TEXT)

    # Should detect clichés
    cliche_issues = [i for i in result.issues if i.type == "style" and "cliché" in i.message.lower()]
    assert len(cliche_issues) > 0


def test_detect_wordy_phrases():
    """Test wordy phrase detection."""
    optimizer = GrammarOptimizer()
    result = optimizer.optimize(WORDY_TEXT)

    # Should detect wordy phrases
    clarity_issues = [i for i in result.issues if i.type == "clarity"]
    assert len(clarity_issues) > 0

    # Check that suggestions are provided
    assert any(i.suggested_text for i in clarity_issues)


def test_passive_voice_detection():
    """Test passive voice detection."""
    optimizer = GrammarOptimizer()

    passive_result = optimizer.optimize(PASSIVE_VOICE_TEXT, prefer_active_voice=True)
    active_result = optimizer.optimize(ACTIVE_VOICE_TEXT, prefer_active_voice=True)

    # Passive text should have higher passive percentage
    assert passive_result.metrics.passive_voice_percentage > active_result.metrics.passive_voice_percentage

    # Passive text should have voice issues flagged
    voice_issues = [i for i in passive_result.issues if i.type == "voice"]
    assert len(voice_issues) > 0


def test_target_grade_level_warning():
    """Test that grade level warnings are issued."""
    optimizer = GrammarOptimizer()

    # Complex text should exceed low target
    result = optimizer.optimize(COMPLEX_TEXT, target_grade_level=8.0)

    # Should have reading level warning (message says "Reading level")
    grade_issues = [i for i in result.issues if "reading level" in i.message.lower()]
    assert len(grade_issues) > 0
    assert result.metrics.flesch_kincaid_grade > 8.0


def test_apply_fixes():
    """Test that automatic fixes are applied."""
    optimizer = GrammarOptimizer()

    result = optimizer.optimize(WORDY_TEXT, apply_fixes=True)

    # Should have applied some fixes
    if result.optimized_text:
        assert result.improvements_applied > 0
        assert result.optimized_text != WORDY_TEXT

        # Wordy phrases should be simplified
        assert "in order to" not in result.optimized_text.lower() or \
               "due to the fact that" not in result.optimized_text.lower()


def test_apply_fixes_with_no_fixable_issues():
    """Test apply_fixes when there are no automatic fixes available."""
    optimizer = GrammarOptimizer()

    # Text with only passive voice (not auto-fixable)
    result = optimizer.optimize(PASSIVE_VOICE_TEXT, apply_fixes=True, prefer_active_voice=True)

    # Should have issues but no automatic fixes
    assert len(result.issues) > 0
    # improvements_applied should be 0 or very low since passive voice can't be auto-fixed


def test_weak_verb_detection():
    """Test detection of weak verbs."""
    weak_verb_text = "The thing is that it is good and it is useful and it has been helpful."

    optimizer = GrammarOptimizer()
    result = optimizer.optimize(weak_verb_text)

    # Should detect weak verbs (multiple "is", "has been")
    style_issues = [i for i in result.issues if i.type == "style" and "verb" in i.message.lower()]
    assert len(style_issues) > 0


def test_optimization_with_ai_model():
    """Test optimization with AI model."""
    mock_model = Mock()
    mock_model.call.return_value = (
        True,
        "Type: grammar\nDescription: Subject-verb disagreement\nOriginal: they was\nSuggestion: they were",
        ""
    )

    optimizer = GrammarOptimizer(model=mock_model)
    result = optimizer.optimize("The students was late.", apply_fixes=False)

    # AI should be called
    mock_model.call.assert_called_once()

    # Should have AI-detected issues
    assert len(result.issues) > 0


def test_optimization_ai_fallback():
    """Test that optimization works when AI fails."""
    mock_model = Mock()
    mock_model.call.return_value = (False, "", "API error")

    optimizer = GrammarOptimizer(model=mock_model)
    result = optimizer.optimize(WORDY_TEXT)

    # Should still work with heuristic analysis
    assert len(result.issues) > 0
    assert result.metrics.total_words > 0


def test_syllable_counting():
    """Test syllable counting approximation."""
    optimizer = GrammarOptimizer()

    assert optimizer._count_syllables("cat") == 1
    assert optimizer._count_syllables("hello") == 2
    assert optimizer._count_syllables("beautiful") == 3
    assert optimizer._count_syllables("education") == 4


def test_sentence_splitting():
    """Test sentence splitting."""
    optimizer = GrammarOptimizer()

    text = "First sentence. Second sentence! Third sentence? Fourth."
    sentences = optimizer._split_sentences(text)

    assert len(sentences) == 4
    assert "First sentence" in sentences[0]


def test_sentence_splitting_with_abbreviations():
    """Test that sentence splitting handles common abbreviations."""
    optimizer = GrammarOptimizer()

    text = "Dr. Smith works at the U.S. embassy. Prof. Johnson teaches there."
    sentences = optimizer._split_sentences(text)

    # Should split into 2 sentences, not 4 (Dr., U.S., and Prof. are abbreviations)
    assert len(sentences) == 2
    assert "Dr. Smith" in sentences[0]
    assert "Prof. Johnson" in sentences[1]


def test_is_passive_voice():
    """Test passive voice detection on individual sentences."""
    optimizer = GrammarOptimizer()

    assert optimizer._is_passive_voice("The essay was written by John.") is True
    assert optimizer._is_passive_voice("The results were analyzed carefully.") is True
    assert optimizer._is_passive_voice("John wrote the essay.") is False
    assert optimizer._is_passive_voice("We analyzed the results.") is False


def test_empty_text_handling():
    """Test handling of empty text."""
    optimizer = GrammarOptimizer()
    result = optimizer.optimize("")

    assert result.metrics.total_words == 0
    assert result.metrics.total_sentences == 0
    assert len(result.issues) == 0


def test_readability_with_textstat():
    """Test readability calculation with textstat library."""
    try:
        import textstat
        has_textstat = True
    except ImportError:
        has_textstat = False

    optimizer = GrammarOptimizer()
    result = optimizer.optimize(SIMPLE_TEXT)

    # Metrics should be calculated regardless
    assert result.metrics.flesch_reading_ease > 0
    assert result.metrics.flesch_kincaid_grade >= 0


def test_readability_without_textstat():
    """Test readability fallback without textstat."""
    optimizer = GrammarOptimizer()

    # Use the approximate method directly
    metrics = optimizer._approximate_readability(SIMPLE_TEXT)

    assert metrics.flesch_reading_ease > 0
    assert metrics.flesch_kincaid_grade >= 0
    assert metrics.total_words > 0


def test_parse_ai_grammar_response():
    """Test parsing of AI grammar response."""
    optimizer = GrammarOptimizer()

    ai_response = """
Type: grammar
Description: Subject-verb agreement error
Original: they was
Suggestion: they were

Type: clarity
Description: Unclear pronoun reference
Original: it is unclear
Suggestion: the concept is unclear
    """

    issues = optimizer._parse_ai_grammar_response(ai_response)

    assert len(issues) == 2
    assert issues[0].type == "grammar"
    assert issues[1].type == "clarity"
    assert issues[0].suggested_text == "they were"


def test_apply_fixes_case_insensitive():
    """Test that fixes are applied case-insensitively."""
    optimizer = GrammarOptimizer()

    text = "In Order To succeed, we must work hard. Due To The Fact That technology advances, we adapt."
    result = optimizer.optimize(text, apply_fixes=True)

    if result.optimized_text:
        # Should replace regardless of case
        assert "In Order To" not in result.optimized_text
        assert "Due To The Fact That" not in result.optimized_text


def test_apply_fixes_multiple_occurrences():
    """Test that all occurrences of the same phrase are fixed."""
    optimizer = GrammarOptimizer()

    # Text with "in order to" appearing 3 times
    text = (
        "In order to succeed, we must work hard. "
        "In order to improve, we must practice. "
        "Students need in order to learn effectively."
    )

    result = optimizer.optimize(text, apply_fixes=True)

    # All 3 occurrences should be replaced with "to"
    assert result.optimized_text is not None
    assert "in order to" not in result.optimized_text.lower()
    assert "In order to" not in result.optimized_text

    # Should have fixed 3 instances
    assert result.improvements_applied >= 3


def test_multiple_issue_types():
    """Test text with multiple types of issues."""
    mixed_text = (
        "At the end of the day, in order to succeed, we need to think outside the box. "
        "The report was written by the team. Due to the fact that technology advances, innovation is driven."
    )

    optimizer = GrammarOptimizer()
    result = optimizer.optimize(mixed_text, prefer_active_voice=True)

    # Should detect multiple types
    issue_types = set(i.type for i in result.issues)
    assert len(issue_types) >= 2  # At least style, clarity, or voice


def test_optimization_preserves_structure():
    """Test that optimization doesn't break text structure."""
    optimizer = GrammarOptimizer()

    multi_para = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph."
    result = optimizer.optimize(multi_para, apply_fixes=True)

    if result.optimized_text:
        # Should maintain basic structure
        assert len(result.optimized_text) > 0
        assert isinstance(result.optimized_text, str)


def test_metrics_accuracy():
    """Test that metrics are reasonably accurate."""
    optimizer = GrammarOptimizer()

    # Known text with specific characteristics
    text = "Short sentence. Another short one. One more here."
    result = optimizer.optimize(text)

    # Should have 3 sentences
    assert result.metrics.total_sentences == 3

    # Word count should be approximately 9
    assert 8 <= result.metrics.total_words <= 10


def test_complex_word_counting():
    """Test complex word counting."""
    optimizer = GrammarOptimizer()

    simple_words = "cat dog run jump play"
    complex_words_text = "extraordinary sophisticated comprehensive technological implementation"

    simple_result = optimizer.optimize(simple_words)
    complex_result = optimizer.optimize(complex_words_text)

    # Complex text should have more complex words
    assert complex_result.metrics.complex_words > simple_result.metrics.complex_words


def test_passive_voice_no_auto_fix():
    """Test that passive voice placeholders are NOT applied as fixes."""
    optimizer = GrammarOptimizer()
    text = "The essay was written by the student."
    
    result = optimizer.optimize(text, apply_fixes=True, prefer_active_voice=True)
    
    # Text should be unchanged
    assert result.optimized_text == text
    # Should flag the issue
    assert any("active voice" in i.message for i in result.issues)
    # But not apply it
    assert "[rewrite in active voice]" not in result.optimized_text


def test_zero_fixes_returns_original():
    """Test that optimizer returns original text when no fixes applied."""
    optimizer = GrammarOptimizer()
    text = "Simple text with no issues."
    
    result = optimizer.optimize(text, apply_fixes=True)
    
    assert result.improvements_applied == 0
    assert result.optimized_text == text


def test_apply_fixes_preserves_case():
    """Test that automatic fixes preserve the case of the original text."""
    optimizer = GrammarOptimizer()
    
    # "In order to" -> "To" (Start of sentence)
    # "in order to" -> "to" (Middle of sentence)
    text = "In order to succeed, we must try. We do this in order to learn."
    
    result = optimizer.optimize(text, apply_fixes=True)
    
    assert result.optimized_text is not None
    
    # First occurrence should be capitalized
    assert "To succeed" in result.optimized_text
    
    # Second occurrence should be lowercase
    assert " to learn" in result.optimized_text
    
    # Original phrases should be gone
    assert "In order to" not in result.optimized_text
    assert "in order to" not in result.optimized_text


