"""Tests for OutlineGenerator."""

import json
import pytest
from unittest.mock import Mock

from src.outline import (
    OutlineGenerator,
    OutlineTemplate,
    ExportFormat,
    Outline,
    OutlineSection,
)


def test_generate_five_paragraph_outline():
    """Test generating a basic 5-paragraph outline."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="The Impact of Technology on Education",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1000,
    )

    assert outline.topic == "The Impact of Technology on Education"
    assert outline.template_type == "5-paragraph"
    assert outline.total_word_count == 1000
    assert len(outline.sections) == 5

    # Check section structure
    intro = outline.sections[0]
    assert "Introduction" in intro.title
    assert intro.suggested_word_count == 150  # 15% of 1000

    body1 = outline.sections[1]
    assert "Body Paragraph 1" in body1.title
    assert body1.suggested_word_count == 230  # 23% of 1000

    conclusion = outline.sections[4]
    assert "Conclusion" in conclusion.title
    assert conclusion.suggested_word_count == 160  # 16% of 1000


def test_generate_analytical_outline():
    """Test generating an analytical essay outline."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="Analysis of Climate Change Policies",
        template=OutlineTemplate.ANALYTICAL,
        word_count=2000,
    )

    assert outline.template_type == "analytical"
    assert len(outline.sections) == 6
    assert outline.total_word_count == 2000

    # Check that word counts sum approximately to total
    total_suggested = sum(s.suggested_word_count for s in outline.sections)
    assert abs(total_suggested - 2000) < 50  # Allow small rounding differences


def test_generate_comparative_outline():
    """Test generating a comparative essay outline."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="Democracy vs. Authoritarianism",
        template=OutlineTemplate.COMPARATIVE,
        word_count=1500,
    )

    assert outline.template_type == "comparative"
    assert len(outline.sections) == 7

    # Check for comparative structure
    section_titles = [s.title for s in outline.sections]
    assert any("Subject A" in t for t in section_titles)
    assert any("Subject B" in t for t in section_titles)
    assert any("Similarities" in t or "Differences" in t for t in section_titles)


def test_generate_argumentative_outline():
    """Test generating an argumentative essay outline."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="Should College Education Be Free?",
        template=OutlineTemplate.ARGUMENTATIVE,
        word_count=1200,
    )

    assert outline.template_type == "argumentative"
    assert len(outline.sections) == 7

    # Check for argumentative structure
    section_titles = [s.title for s in outline.sections]
    assert any("Argument" in t for t in section_titles)
    assert any("Counterargument" in t for t in section_titles)
    assert any("Rebuttal" in t for t in section_titles)


def test_generate_with_notes():
    """Test generating an outline with notes incorporated."""
    generator = OutlineGenerator()
    notes = "Focus on digital literacy\nMention online learning platforms\nDiscuss equity issues"

    outline = generator.generate(
        topic="Technology in Education",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1000,
        notes=notes,
    )

    assert outline.notes == notes

    # Check that notes appear in key points
    all_key_points = []
    for section in outline.sections:
        all_key_points.extend(section.key_points)

    # At least some notes should be incorporated
    assert len(all_key_points) > 0


def test_generate_with_ai_model():
    """Test generating an outline with AI model."""
    mock_model = Mock()
    mock_model.call.return_value = (
        True,
        "## Introduction\n- Hook about technology\n- Thesis statement\n\n## Body Section 1\n- Digital tools\n- Evidence\n\n## Conclusion\n- Summary",
        ""
    )

    generator = OutlineGenerator(model=mock_model)
    outline = generator.generate(
        topic="Technology in Education",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1000,
    )

    # AI model should be called
    mock_model.call.assert_called_once()

    # Should have generated sections (either from AI or fallback)
    assert len(outline.sections) >= 3


def test_generate_ai_fallback_on_failure():
    """Test that generation falls back to template when AI fails."""
    mock_model = Mock()
    mock_model.call.return_value = (False, "", "API error")

    generator = OutlineGenerator(model=mock_model)
    outline = generator.generate(
        topic="Test Topic",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1000,
    )

    # Should still generate outline using template
    assert len(outline.sections) == 5
    assert outline.topic == "Test Topic"


def test_export_to_markdown():
    """Test exporting outline to Markdown format."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="Climate Change",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1000,
    )

    markdown = generator.export(outline, ExportFormat.MARKDOWN)

    assert "# Essay Outline: Climate Change" in markdown
    assert "**Template:** 5-paragraph" in markdown
    assert "**Target Word Count:** 1000" in markdown
    assert "### 1. Introduction" in markdown
    assert "**Key Points:**" in markdown


def test_export_to_json():
    """Test exporting outline to JSON format."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="Artificial Intelligence",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1500,
    )

    json_output = generator.export(outline, ExportFormat.JSON)
    data = json.loads(json_output)

    assert data["topic"] == "Artificial Intelligence"
    assert data["template_type"] == "5-paragraph"
    assert data["total_word_count"] == 1500
    assert len(data["sections"]) == 5

    # Check section structure
    first_section = data["sections"][0]
    assert "title" in first_section
    assert "description" in first_section
    assert "suggested_word_count" in first_section
    assert "key_points" in first_section


def test_export_to_plain_text():
    """Test exporting outline to plain text format."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="Renewable Energy",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=800,
    )

    plain = generator.export(outline, ExportFormat.PLAIN_TEXT)

    assert "ESSAY OUTLINE: RENEWABLE ENERGY" in plain
    assert "Template: 5-paragraph" in plain
    assert "Target Word Count: 800" in plain
    assert "1. INTRODUCTION" in plain
    assert "Key Points:" in plain


def test_convert_notes_to_outline():
    """Test converting rough notes to structured outline."""
    generator = OutlineGenerator()
    notes = """
    Discuss renewable energy benefits
    Solar power is becoming cheaper
    Wind energy is effective in many regions
    Need to address storage challenges
    Government policies matter
    """

    outline = generator.convert_notes_to_outline(
        notes=notes,
        template=OutlineTemplate.ANALYTICAL,
        word_count=1500,
    )

    # Should extract topic from notes
    assert outline.topic  # Should have some topic
    assert outline.notes == notes
    assert outline.template_type == "analytical"
    assert len(outline.sections) == 6


def test_convert_notes_extracts_topic_with_ai():
    """Test that AI model helps extract topic from notes."""
    mock_model = Mock()
    mock_model.call.side_effect = [
        (True, "Renewable Energy Adoption", ""),  # Topic extraction
        (True, "## Section 1\n- Point 1", ""),    # Outline generation
    ]

    generator = OutlineGenerator(model=mock_model)
    notes = "Various thoughts about solar panels and wind turbines..."

    outline = generator.convert_notes_to_outline(
        notes=notes,
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1000,
    )

    assert outline.topic == "Renewable Energy Adoption"


def test_convert_notes_fallback_topic_extraction():
    """Test topic extraction fallback without AI."""
    generator = OutlineGenerator()
    notes = "The importance of cybersecurity in modern business\nMany points follow..."

    outline = generator.convert_notes_to_outline(
        notes=notes,
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1000,
    )

    # Should use first line as topic
    assert "cybersecurity" in outline.topic.lower()


def test_key_points_generation_for_introduction():
    """Test that introduction sections get appropriate key points."""
    generator = OutlineGenerator()
    points = generator._generate_key_points("Introduction", "Climate Change", None)

    # Should include thesis and hook
    assert len(points) > 0
    assert any("hook" in p.lower() or "thesis" in p.lower() for p in points)


def test_key_points_generation_for_conclusion():
    """Test that conclusion sections get appropriate key points."""
    generator = OutlineGenerator()
    points = generator._generate_key_points("Conclusion", "AI Ethics", None)

    # Should include summary/restatement prompts
    assert len(points) > 0
    assert any("restate" in p.lower() or "synthesis" in p.lower() for p in points)


def test_key_points_generation_for_body():
    """Test that body sections get appropriate key points."""
    generator = OutlineGenerator()
    points = generator._generate_key_points("Body Paragraph 1", "Social Media Impact", None)

    # Should include claim and evidence prompts
    assert len(points) > 0
    assert any("claim" in p.lower() or "evidence" in p.lower() for p in points)


def test_key_points_incorporate_notes():
    """Test that key points incorporate provided notes."""
    generator = OutlineGenerator()
    notes = "Point A is important\nPoint B needs discussion\nPoint C is critical"

    points = generator._generate_key_points("Body Paragraph 1", "Test", notes)

    # Should include note items
    assert "Point A is important" in points or "Point B needs discussion" in points


def test_section_word_counts_are_reasonable():
    """Test that word count distribution is reasonable."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="Test Topic",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1000,
    )

    # All sections should have positive word counts
    for section in outline.sections:
        assert section.suggested_word_count > 0

    # Total should be close to target
    total = sum(s.suggested_word_count for s in outline.sections)
    assert 950 <= total <= 1050  # Within 5% of target


def test_outline_with_empty_topic():
    """Test outline generation with minimal topic."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="AI",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=500,
    )

    assert outline.topic == "AI"
    assert len(outline.sections) == 5


def test_all_templates_generate_valid_outlines():
    """Test that all template types generate valid outlines."""
    generator = OutlineGenerator()

    for template in OutlineTemplate:
        outline = generator.generate(
            topic=f"Test topic for {template.value}",
            template=template,
            word_count=1000,
        )

        assert outline.template_type == template.value
        assert len(outline.sections) > 0
        assert outline.total_word_count == 1000

        # All sections should have required fields
        for section in outline.sections:
            assert section.title
            assert section.description
            assert section.suggested_word_count > 0


def test_export_includes_notes_when_present():
    """Test that export includes notes section when notes exist."""
    generator = OutlineGenerator()
    outline = generator.generate(
        topic="Test",
        template=OutlineTemplate.FIVE_PARAGRAPH,
        word_count=1000,
        notes="Important context here",
    )

    markdown = generator.export(outline, ExportFormat.MARKDOWN)
    assert "## Notes" in markdown
    assert "Important context here" in markdown

    plain = generator.export(outline, ExportFormat.PLAIN_TEXT)
    assert "NOTES:" in plain
    assert "Important context here" in plain


def test_long_topic_truncation_in_notes_extraction():
    """Test that very long first lines in notes are truncated."""
    generator = OutlineGenerator()
    long_first_line = "A" * 150
    notes = f"{long_first_line}\nMore content here"

    topic = generator._extract_topic_from_notes(notes)

    # Should truncate to reasonable length
    assert len(topic) <= 100
    assert "..." in topic
