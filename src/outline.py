"""Smart Outline Generator."""

import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .models.base import AIModel

logger = logging.getLogger(__name__)


class OutlineTemplate(Enum):
    """Available outline templates."""

    FIVE_PARAGRAPH = "5-paragraph"
    ANALYTICAL = "analytical"
    COMPARATIVE = "comparative"
    ARGUMENTATIVE = "argumentative"


class ExportFormat(Enum):
    """Available export formats."""

    MARKDOWN = "markdown"
    JSON = "json"
    PLAIN_TEXT = "plain"


@dataclass
class OutlineSection:
    """A single section in an outline."""

    title: str
    description: str
    suggested_word_count: int
    subsections: List[str]
    key_points: List[str]


@dataclass
class Outline:
    """Complete essay outline."""

    topic: str
    template_type: str
    total_word_count: int
    sections: List[OutlineSection]
    notes: Optional[str] = None


class OutlineGenerator:
    """Generate structured essay outlines from topics or notes."""

    # Template configurations with section counts and proportions
    TEMPLATES = {
        OutlineTemplate.FIVE_PARAGRAPH: {
            "sections": [
                ("Introduction", "Hook, background, and thesis statement", 0.15),
                ("Body Paragraph 1", "First main point with evidence", 0.23),
                ("Body Paragraph 2", "Second main point with evidence", 0.23),
                ("Body Paragraph 3", "Third main point with evidence", 0.23),
                ("Conclusion", "Restate thesis, summarize points, closing thoughts", 0.16),
            ],
            "description": "Classic five-paragraph essay structure"
        },
        OutlineTemplate.ANALYTICAL: {
            "sections": [
                ("Introduction", "Context, thesis, and analytical framework", 0.12),
                ("Background/Context", "Historical or theoretical background", 0.15),
                ("Analysis Section 1", "First dimension of analysis", 0.20),
                ("Analysis Section 2", "Second dimension of analysis", 0.20),
                ("Analysis Section 3", "Third dimension of analysis", 0.20),
                ("Conclusion", "Synthesis of analysis and implications", 0.13),
            ],
            "description": "In-depth analytical essay structure"
        },
        OutlineTemplate.COMPARATIVE: {
            "sections": [
                ("Introduction", "Introduce subjects and comparison thesis", 0.12),
                ("Subject A Overview", "Key characteristics of first subject", 0.15),
                ("Subject B Overview", "Key characteristics of second subject", 0.15),
                ("Similarities", "Points of comparison and common ground", 0.20),
                ("Differences", "Contrasting elements and distinctions", 0.20),
                ("Significance", "Implications of the comparison", 0.10),
                ("Conclusion", "Summary and final assessment", 0.08),
            ],
            "description": "Compare and contrast essay structure"
        },
        OutlineTemplate.ARGUMENTATIVE: {
            "sections": [
                ("Introduction", "Hook, background, clear thesis/claim", 0.12),
                ("Argument 1", "First supporting argument with evidence", 0.18),
                ("Argument 2", "Second supporting argument with evidence", 0.18),
                ("Argument 3", "Third supporting argument with evidence", 0.18),
                ("Counterargument", "Address opposing views", 0.15),
                ("Rebuttal", "Refute counterargument", 0.10),
                ("Conclusion", "Restate thesis, call to action", 0.09),
            ],
            "description": "Persuasive argumentative essay structure"
        },
    }

    def __init__(self, model: Optional[AIModel] = None):
        """
        Initialize the outline generator.

        Args:
            model: Optional AI model for intelligent outline generation.
        """
        self.model = model

    def generate(
        self,
        topic: str,
        template: OutlineTemplate = OutlineTemplate.FIVE_PARAGRAPH,
        word_count: int = 1000,
        notes: Optional[str] = None,
    ) -> Outline:
        """
        Generate a structured outline.

        Args:
            topic: Essay topic or prompt.
            template: Outline template to use.
            word_count: Target word count for the essay.
            notes: Optional rough notes to incorporate.

        Returns:
            Structured Outline object.
        """
        template_config = self.TEMPLATES[template]
        sections: List[OutlineSection] = []

        # If AI model available, generate intelligent sections
        if self.model:
            sections = self._generate_ai_sections(topic, template, word_count, notes)

        # Fall back to template-based generation
        if not sections:
            sections = self._generate_template_sections(
                topic, template_config, word_count, notes
            )

        return Outline(
            topic=topic,
            template_type=template.value,
            total_word_count=word_count,
            sections=sections,
            notes=notes,
        )

    def _generate_ai_sections(
        self,
        topic: str,
        template: OutlineTemplate,
        word_count: int,
        notes: Optional[str],
    ) -> List[OutlineSection]:
        """Generate sections using AI model."""
        template_config = self.TEMPLATES[template]
        template_desc = template_config["description"]

        prompt = (
            f"Generate a detailed essay outline for the following topic:\n\n"
            f"Topic: {topic}\n"
            f"Template: {template_desc}\n"
            f"Target word count: {word_count}\n"
        )

        if notes:
            prompt += f"\nIncorporate these notes:\n{notes}\n"

        prompt += (
            f"\nFor each section, provide:\n"
            f"1. A clear title\n"
            f"2. A brief description of what to cover\n"
            f"3. 2-4 key points or subsections\n\n"
            f"Format your response as a structured outline."
        )

        success, response, error = self.model.call(prompt)

        if not success or not response.strip():
            logger.warning("AI outline generation failed: %s", error)
            return []

        # Parse AI response into sections
        return self._parse_ai_response(response, template_config, word_count)

    def _parse_ai_response(
        self,
        response: str,
        template_config: Dict,
        word_count: int,
    ) -> List[OutlineSection]:
        """Parse AI-generated outline response."""
        sections: List[OutlineSection] = []
        lines = response.strip().split('\n')

        current_section = None
        current_points = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for section headers (various formats)
            if any(marker in line for marker in ['##', '**', 'Section:', 'I.', 'A.', '1.']):
                # Save previous section
                if current_section:
                    sections.append(current_section)

                # Start new section
                title = line.strip('#* ').strip()
                if ':' in title:
                    title = title.split(':', 1)[1].strip()

                # Get word count proportion from template
                section_idx = len(sections)
                if section_idx < len(template_config["sections"]):
                    _, desc, proportion = template_config["sections"][section_idx]
                    wc = int(word_count * proportion)
                else:
                    desc = "Additional section"
                    wc = 100

                current_section = OutlineSection(
                    title=title,
                    description=desc,
                    suggested_word_count=wc,
                    subsections=[],
                    key_points=[],
                )
                current_points = []

            # Look for bullet points or key points
            elif line.startswith(('-', '*', '•')) and current_section:
                point = line.lstrip('-*• ').strip()
                current_section.key_points.append(point)

        # Save last section
        if current_section:
            sections.append(current_section)

        return sections if sections else []

    def _generate_template_sections(
        self,
        topic: str,
        template_config: Dict,
        word_count: int,
        notes: Optional[str],
    ) -> List[OutlineSection]:
        """Generate sections based on template structure."""
        sections: List[OutlineSection] = []

        for title, description, proportion in template_config["sections"]:
            section_word_count = int(word_count * proportion)

            # Generate generic key points based on section type
            key_points = self._generate_key_points(title, topic, notes)

            sections.append(
                OutlineSection(
                    title=title,
                    description=description,
                    suggested_word_count=section_word_count,
                    subsections=[],
                    key_points=key_points,
                )
            )

        return sections

    def _generate_key_points(
        self,
        section_title: str,
        topic: str,
        notes: Optional[str],
    ) -> List[str]:
        """Generate key points for a section."""
        points: List[str] = []

        # Extract relevant notes if available
        if notes:
            note_lines = [line.strip() for line in notes.split('\n') if line.strip()]
            points.extend(note_lines[:3])  # Include up to 3 note items

        # Add generic prompts based on section type
        if "Introduction" in section_title:
            if not any("hook" in p.lower() for p in points):
                points.append(f"Opening hook related to {topic}")
            if not any("thesis" in p.lower() for p in points):
                points.append("Clear thesis statement")
        elif "Conclusion" in section_title:
            if not any("restate" in p.lower() for p in points):
                points.append("Restate main thesis")
            points.append("Synthesize key arguments")
            points.append("Final thoughts or call to action")
        elif "Body" in section_title or "Argument" in section_title:
            if not points:
                points.append(f"Main claim related to {topic}")
                points.append("Supporting evidence or examples")
                points.append("Analysis connecting evidence to thesis")

        return points[:5]  # Limit to 5 key points per section

    def export(self, outline: Outline, format: ExportFormat) -> str:
        """
        Export outline in specified format.

        Args:
            outline: The outline to export.
            format: Export format (markdown, JSON, plain text).

        Returns:
            Formatted outline string.
        """
        if format == ExportFormat.JSON:
            return self._export_json(outline)
        elif format == ExportFormat.MARKDOWN:
            return self._export_markdown(outline)
        else:
            return self._export_plain(outline)

    def _export_json(self, outline: Outline) -> str:
        """Export outline as JSON."""
        data = asdict(outline)
        return json.dumps(data, indent=2)

    def _export_markdown(self, outline: Outline) -> str:
        """Export outline as Markdown."""
        lines = [
            f"# Essay Outline: {outline.topic}",
            f"",
            f"**Template:** {outline.template_type}  ",
            f"**Target Word Count:** {outline.total_word_count}  ",
            f"",
        ]

        if outline.notes:
            lines.extend([
                "## Notes",
                "",
                outline.notes,
                "",
            ])

        lines.append("## Outline")
        lines.append("")

        for i, section in enumerate(outline.sections, 1):
            lines.append(f"### {i}. {section.title}")
            lines.append(f"*{section.description}*  ")
            lines.append(f"**Suggested word count:** {section.suggested_word_count}")
            lines.append("")

            if section.key_points:
                lines.append("**Key Points:**")
                for point in section.key_points:
                    lines.append(f"- {point}")
                lines.append("")

            if section.subsections:
                lines.append("**Subsections:**")
                for subsection in section.subsections:
                    lines.append(f"- {subsection}")
                lines.append("")

        return "\n".join(lines)

    def _export_plain(self, outline: Outline) -> str:
        """Export outline as plain text."""
        lines = [
            "=" * 60,
            f"ESSAY OUTLINE: {outline.topic.upper()}",
            "=" * 60,
            f"Template: {outline.template_type}",
            f"Target Word Count: {outline.total_word_count}",
            "",
        ]

        if outline.notes:
            lines.extend([
                "NOTES:",
                "-" * 60,
                outline.notes,
                "",
            ])

        lines.append("OUTLINE:")
        lines.append("-" * 60)

        for i, section in enumerate(outline.sections, 1):
            lines.append(f"\n{i}. {section.title.upper()}")
            lines.append(f"   {section.description}")
            lines.append(f"   Word count: ~{section.suggested_word_count} words")

            if section.key_points:
                lines.append("   Key Points:")
                for point in section.key_points:
                    lines.append(f"     • {point}")

            if section.subsections:
                lines.append("   Subsections:")
                for subsection in section.subsections:
                    lines.append(f"     - {subsection}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def convert_notes_to_outline(
        self,
        notes: str,
        template: OutlineTemplate = OutlineTemplate.FIVE_PARAGRAPH,
        word_count: int = 1000,
    ) -> Outline:
        """
        Convert rough notes into a structured outline.

        Args:
            notes: Unstructured notes or brainstorming content.
            template: Template to structure the notes with.
            word_count: Target word count.

        Returns:
            Structured Outline.
        """
        # Extract topic from notes (first line or AI-generated)
        topic = self._extract_topic_from_notes(notes)

        return self.generate(
            topic=topic,
            template=template,
            word_count=word_count,
            notes=notes,
        )

    def _extract_topic_from_notes(self, notes: str) -> str:
        """Extract or infer topic from notes."""
        if self.model:
            prompt = (
                f"Based on these notes, what is the main essay topic? "
                f"Respond with ONLY the topic in 10 words or less.\n\n{notes}"
            )
            success, response, _ = self.model.call(prompt)
            if success and response.strip():
                return response.strip()

        # Fallback: use first line or first sentence
        lines = [line.strip() for line in notes.split('\n') if line.strip()]
        if lines:
            first_line = lines[0]
            # Limit length
            if len(first_line) > 100:
                return first_line[:97] + "..."
            return first_line

        return "Essay Topic"
