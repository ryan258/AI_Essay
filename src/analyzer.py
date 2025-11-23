"""Essay Structure Analyzer module."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table

from .models.base import AIModel

# Configure logging
logger = logging.getLogger(__name__)
console = Console()

@dataclass
class ParagraphAnalysis:
    """Analysis of a single paragraph."""
    number: int
    word_count: int
    has_topic_sentence: bool
    topic_sentence: Optional[str]
    strength: str  # "strong", "moderate", "weak"
    issues: List[str]
    is_body: bool = False  # Whether this is a body paragraph (not intro/conclusion)

@dataclass
class EssayStructure:
    """Complete essay structure analysis."""
    has_introduction: bool
    has_conclusion: bool
    thesis_statement: Optional[str]
    thesis_location: Optional[str]  # "introduction", "conclusion", "missing"
    paragraph_count: int
    body_paragraph_count: int
    total_word_count: int
    paragraphs: List[ParagraphAnalysis]
    transition_quality: str  # "strong", "moderate", "weak"
    overall_score: float  # 0-100
    recommendations: List[str]

class EssayAnalyzer:
    """Analyzes essay structure and provides recommendations."""

    def __init__(self, model: Optional[AIModel] = None):
        """
        Initialize the analyzer.

        Args:
            model: AIModel instance for AI-powered analysis (optional)
        """
        self.model = model

    def analyze(self, essay_text: str) -> EssayStructure:
        """
        Analyze essay structure.

        Args:
            essay_text: The essay text to analyze

        Returns:
            EssayStructure with complete analysis
        """
        # Split into paragraphs
        paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]

        if not paragraphs:
            return self._create_empty_structure()

        # Analyze each component
        has_intro = self._detect_introduction(paragraphs[0])
        has_conclusion = self._detect_conclusion(paragraphs[-1]) if len(paragraphs) > 1 else False
        thesis, thesis_loc = self._extract_thesis(paragraphs, has_intro, has_conclusion)

        # Analyze paragraphs
        paragraph_analyses = []
        body_start = 1 if has_intro else 0
        body_end = len(paragraphs) - 1 if has_conclusion else len(paragraphs)

        for i, para in enumerate(paragraphs):
            is_body = body_start <= i < body_end
            analysis = self._analyze_paragraph(i + 1, para, is_body)
            paragraph_analyses.append(analysis)

        # Calculate metrics
        total_words = sum(len(p.split()) for p in paragraphs)
        body_count = body_end - body_start
        transition_quality = self._assess_transitions(paragraphs)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            has_intro, has_conclusion, thesis, paragraph_analyses, transition_quality
        )

        # Calculate overall score
        score = self._calculate_score(
            has_intro, has_conclusion, thesis, paragraph_analyses, transition_quality
        )

        return EssayStructure(
            has_introduction=has_intro,
            has_conclusion=has_conclusion,
            thesis_statement=thesis,
            thesis_location=thesis_loc,
            paragraph_count=len(paragraphs),
            body_paragraph_count=body_count,
            total_word_count=total_words,
            paragraphs=paragraph_analyses,
            transition_quality=transition_quality,
            overall_score=score,
            recommendations=recommendations
        )

    def _detect_introduction(self, first_para: str) -> bool:
        """Detect if first paragraph is a proper introduction."""
        words = first_para.split()
        word_count = len(words)

        # Simple heuristics
        if word_count < 30:
            return False

        # Look for introduction markers
        intro_markers = ["this essay", "this paper", "will discuss", "will explore",
                        "will examine", "in this", "purpose of this"]
        text_lower = first_para.lower()

        return any(marker in text_lower for marker in intro_markers)

    def _detect_conclusion(self, last_para: str) -> bool:
        """Detect if last paragraph is a proper conclusion."""
        words = last_para.split()
        word_count = len(words)

        if word_count < 20:
            return False

        # Look for conclusion markers
        conclusion_markers = ["in conclusion", "to conclude", "in summary",
                             "to summarize", "ultimately", "in the end",
                             "therefore", "thus"]
        text_lower = last_para.lower()

        return any(marker in text_lower for marker in conclusion_markers)

    def _extract_thesis(self, paragraphs: List[str], has_intro: bool, has_conclusion: bool) -> tuple[Optional[str], Optional[str]]:
        """Extract thesis statement and its location."""
        if not self.model:
            # Simple heuristic: last sentence of intro
            if has_intro and paragraphs:
                sentences = paragraphs[0].split('.')
                if len(sentences) > 1:
                    thesis = sentences[-2].strip() + '.'
                    return thesis, "introduction"
            return None, "missing"

        # AI-powered extraction
        prompt = (
            "Identify the thesis statement in the following essay. "
            "Return ONLY the thesis statement, nothing else. "
            "If there is no clear thesis, return 'NO_THESIS'.\n\n"
            f"Essay:\n{' '.join(paragraphs[:3])[:1000]}..."  # First few paragraphs
        )

        success, response, error = self.model.call(prompt)
        if success and response.strip() != "NO_THESIS":
            # Determine location
            if response.lower() in paragraphs[0].lower():
                location = "introduction"
            elif has_conclusion and response.lower() in paragraphs[-1].lower():
                location = "conclusion"
            else:
                location = "body"
            return response.strip(), location

        return None, "missing"

    def _analyze_paragraph(self, number: int, para: str, is_body: bool) -> ParagraphAnalysis:
        """Analyze a single paragraph."""
        words = para.split()
        word_count = len(words)
        sentences = para.split('.')

        # Extract potential topic sentence (first sentence)
        topic_sentence = sentences[0].strip() + '.' if sentences else None

        # Simple heuristic for topic sentence quality
        has_topic = False
        strength = "weak"
        issues = []

        if is_body:
            if word_count < 50:
                issues.append("Too short (under 50 words)")
                strength = "weak"
            elif word_count > 250:
                issues.append("Too long (over 250 words)")
                strength = "moderate"
            else:
                strength = "moderate"

            if topic_sentence and len(topic_sentence.split()) > 8:
                has_topic = True
                if len(sentences) > 3:
                    strength = "strong"
            else:
                issues.append("Weak or missing topic sentence")
                has_topic = False

        return ParagraphAnalysis(
            number=number,
            word_count=word_count,
            has_topic_sentence=has_topic,
            topic_sentence=topic_sentence,
            strength=strength,
            issues=issues,
            is_body=is_body
        )

    def _assess_transitions(self, paragraphs: List[str]) -> str:
        """Assess quality of transitions between paragraphs."""
        if len(paragraphs) < 2:
            return "weak"

        transition_words = [
            "however", "moreover", "furthermore", "additionally", "nevertheless",
            "consequently", "therefore", "thus", "meanwhile", "similarly",
            "in contrast", "on the other hand", "for example", "for instance"
        ]

        transition_count = 0
        for para in paragraphs[1:]:  # Skip first paragraph
            first_sentence = para.split('.')[0].lower()
            if any(word in first_sentence for word in transition_words):
                transition_count += 1

        ratio = transition_count / (len(paragraphs) - 1)

        if ratio >= 0.6:
            return "strong"
        elif ratio >= 0.3:
            return "moderate"
        else:
            return "weak"

    def _generate_recommendations(
        self,
        has_intro: bool,
        has_conclusion: bool,
        thesis: Optional[str],
        paragraphs: List[ParagraphAnalysis],
        transition_quality: str
    ) -> List[str]:
        """Generate improvement recommendations."""
        recs = []

        if not has_intro:
            recs.append("Add a clear introduction paragraph")

        if not has_conclusion:
            recs.append("Add a conclusion to summarize your argument")

        if thesis is None:
            recs.append("Include a clear thesis statement")

        # Check body paragraphs only (exclude intro/conclusion)
        body_paras = [p for p in paragraphs if p.is_body]
        weak_body_paras = [p for p in body_paras if p.strength == "weak"]
        if weak_body_paras:
            recs.append(f"Strengthen {len(weak_body_paras)} weak body paragraph(s)")

        # Check topic sentences in body paragraphs only
        missing_topics = [p for p in body_paras if not p.has_topic_sentence and p.issues]
        if missing_topics:
            recs.append(f"Add clear topic sentences to {len(missing_topics)} paragraph(s)")

        # Check transitions
        if transition_quality == "weak":
            recs.append("Improve transitions between paragraphs")
        elif transition_quality == "moderate":
            recs.append("Consider adding more transition words")

        if not recs:
            recs.append("Essay structure looks good! Consider minor polish.")

        return recs

    def _calculate_score(
        self,
        has_intro: bool,
        has_conclusion: bool,
        thesis: Optional[str],
        paragraphs: List[ParagraphAnalysis],
        transition_quality: str
    ) -> float:
        """Calculate overall structure score (0-100)."""
        score = 0.0

        # Introduction (20 points)
        if has_intro:
            score += 20

        # Conclusion (15 points)
        if has_conclusion:
            score += 15

        # Thesis (25 points)
        if thesis:
            score += 25

        # Body paragraphs (30 points) - only score actual body paragraphs
        body_paras = [p for p in paragraphs if p.is_body]
        if body_paras:
            strong_count = len([p for p in body_paras if p.strength == "strong"])
            moderate_count = len([p for p in body_paras if p.strength == "moderate"])

            body_score = (strong_count * 1.0 + moderate_count * 0.6) / len(body_paras)
            score += body_score * 30

        # Transitions (10 points)
        if transition_quality == "strong":
            score += 10
        elif transition_quality == "moderate":
            score += 6
        else:
            score += 2

        return min(100.0, score)

    def _create_empty_structure(self) -> EssayStructure:
        """Create empty structure for invalid input."""
        return EssayStructure(
            has_introduction=False,
            has_conclusion=False,
            thesis_statement=None,
            thesis_location="missing",
            paragraph_count=0,
            body_paragraph_count=0,
            total_word_count=0,
            paragraphs=[],
            transition_quality="weak",
            overall_score=0.0,
            recommendations=["Provide essay text to analyze"]
        )

    def print_analysis(self, structure: EssayStructure) -> None:
        """Print formatted analysis to console."""
        console.print("\n[bold cyan]Essay Structure Analysis[/bold cyan]")
        console.print("=" * 60)

        # Overall metrics
        console.print(f"\n[bold]Overall Score:[/bold] {structure.overall_score:.1f}/100")
        console.print(f"[bold]Total Words:[/bold] {structure.total_word_count}")
        console.print(f"[bold]Paragraphs:[/bold] {structure.paragraph_count} ({structure.body_paragraph_count} body)")

        # Structure components
        console.print(f"\n[bold]Structure:[/bold]")
        intro_status = "✅" if structure.has_introduction else "❌"
        console.print(f"  {intro_status} Introduction")

        thesis_status = "✅" if structure.thesis_statement else "❌"
        console.print(f"  {thesis_status} Thesis Statement", end="")
        if structure.thesis_statement:
            console.print(f" ({structure.thesis_location})")
        else:
            console.print()

        conclusion_status = "✅" if structure.has_conclusion else "❌"
        console.print(f"  {conclusion_status} Conclusion")

        # Transitions
        trans_color = {
            "strong": "green",
            "moderate": "yellow",
            "weak": "red"
        }[structure.transition_quality]
        console.print(f"  Transitions: [{trans_color}]{structure.transition_quality.upper()}[/{trans_color}]")

        # Thesis statement
        if structure.thesis_statement:
            console.print(f"\n[bold]Thesis:[/bold]")
            console.print(f'  "{structure.thesis_statement}"')

        # Paragraph details
        if structure.paragraphs:
            console.print(f"\n[bold]Paragraph Analysis:[/bold]")

            table = Table(show_header=True, header_style="bold")
            table.add_column("#", width=4)
            table.add_column("Words", width=8)
            table.add_column("Strength", width=10)
            table.add_column("Topic Sentence", width=8)
            table.add_column("Issues", width=30)

            for p in structure.paragraphs:
                strength_color = {
                    "strong": "green",
                    "moderate": "yellow",
                    "weak": "red"
                }[p.strength]

                topic_icon = "✅" if p.has_topic_sentence else "❌"
                issues_text = ", ".join(p.issues) if p.issues else "None"

                table.add_row(
                    str(p.number),
                    str(p.word_count),
                    f"[{strength_color}]{p.strength}[/{strength_color}]",
                    topic_icon,
                    issues_text
                )

            console.print(table)

        # Recommendations
        if structure.recommendations:
            console.print(f"\n[bold yellow]Recommendations:[/bold yellow]")
            for i, rec in enumerate(structure.recommendations, 1):
                console.print(f"  {i}. {rec}")

        console.print()
