"""Argument Analyzer & Strengthener."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .models.base import AIModel

logger = logging.getLogger(__name__)


@dataclass
class Claim:
    """A specific claim made in the argument."""

    text: str
    type: str  # "thesis", "supporting", "counter"
    strength: str  # "strong", "moderate", "weak"
    evidence: Optional[str] = None
    explanation: Optional[str] = None


@dataclass
class Fallacy:
    """A detected logical fallacy."""

    name: str
    description: str
    text: str
    explanation: str


@dataclass
class ArgumentAnalysis:
    """Full analysis of an essay's argumentation."""

    thesis: Optional[str]
    claims: List[Claim] = field(default_factory=list)
    fallacies: List[Fallacy] = field(default_factory=list)
    overall_strength: float = 0.0  # 0-10 scale
    critique: str = ""
    suggestions: List[str] = field(default_factory=list)


class ArgumentAnalyzer:
    """Analyzes and strengthens arguments in essays."""

    def __init__(self, model: Optional[AIModel] = None):
        """
        Initialize the analyzer.

        Args:
            model: AI model for analysis.
        """
        self.model = model

    def analyze(self, text: str) -> ArgumentAnalysis:
        """
        Analyze the argumentation in the text.

        Args:
            text: The essay text to analyze.

        Returns:
            ArgumentAnalysis object containing the results.
        """
        if not text or not text.strip():
            return ArgumentAnalysis(thesis=None, critique="No text provided.")

        if not self.model:
            logger.warning("No AI model provided for argument analysis.")
            return ArgumentAnalysis(thesis=None, critique="AI model required for argument analysis.")

        # 1. Extract structure (Thesis & Claims)
        structure = self._extract_structure(text)
        
        # 2. Detect fallacies
        fallacies = self._detect_fallacies(text)
        
        # 3. Evaluate strength and get suggestions
        evaluation = self._evaluate_strength(text, structure, fallacies)

        return ArgumentAnalysis(
            thesis=structure.get("thesis"),
            claims=structure.get("claims", []),
            fallacies=fallacies,
            overall_strength=evaluation.get("score", 0.0),
            critique=evaluation.get("critique", ""),
            suggestions=evaluation.get("suggestions", []),
        )

    def _extract_structure(self, text: str) -> Dict[str, Any]:
        """Extract thesis and supporting claims."""
        prompt = (
            "Analyze the argument structure of the following text.\n"
            "Identify the main thesis statement and the key supporting claims.\n"
            "For each claim, assess its strength (strong/moderate/weak) and identify any evidence used.\n\n"
            "Format your response exactly as follows:\n"
            "Thesis: [The main thesis statement]\n\n"
            "Claim 1: [Claim text]\n"
            "Type: [supporting/counter]\n"
            "Strength: [strong/moderate/weak]\n"
            "Evidence: [Brief description of evidence or 'None']\n"
            "Explanation: [Why it is strong/weak]\n\n"
            "Claim 2: ...\n\n"
            f"Text:\n{text}"
        )

        success, response, _ = self.model.call(prompt)
        if not success:
            return {"thesis": None, "claims": []}

        return self._parse_structure_response(response)

    def _parse_structure_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response for structure."""
        lines = response.strip().split('\n')
        thesis = None
        claims = []
        current_claim = {}

        for line in lines:
            line = line.strip()
            if not line:
                if current_claim:
                    claims.append(Claim(**current_claim))
                    current_claim = {}
                continue

            if line.startswith("Thesis:"):
                thesis = line.replace("Thesis:", "").strip()
            elif line.startswith("Claim") and ":" in line:
                if current_claim and "text" in current_claim:
                    claims.append(Claim(**current_claim))
                # Reset with defaults
                current_claim = {
                    "text": line.split(":", 1)[1].strip(),
                    "type": "supporting",
                    "strength": "moderate"
                }
            elif line.startswith("Type:"):
                current_claim["type"] = line.replace("Type:", "").strip().lower()
            elif line.startswith("Strength:"):
                current_claim["strength"] = line.replace("Strength:", "").strip().lower()
            elif line.startswith("Evidence:"):
                current_claim["evidence"] = line.replace("Evidence:", "").strip()
            elif line.startswith("Explanation:"):
                current_claim["explanation"] = line.replace("Explanation:", "").strip()

        if current_claim and "text" in current_claim:
            claims.append(Claim(**current_claim))

        return {"thesis": thesis, "claims": claims}

    def _detect_fallacies(self, text: str) -> List[Fallacy]:
        """Detect logical fallacies."""
        prompt = (
            "Identify any logical fallacies in the following text.\n"
            "Look for common fallacies like Ad Hominem, Straw Man, Slippery Slope, Circular Reasoning, Hasty Generalization, etc.\n"
            "If no fallacies are found, reply with 'No fallacies found.'\n\n"
            "Format each fallacy as:\n"
            "Fallacy: [Name of fallacy]\n"
            "Text: [The specific text containing the fallacy]\n"
            "Explanation: [Why this is a fallacy]\n\n"
            f"Text:\n{text}"
        )

        success, response, _ = self.model.call(prompt)
        if not success or "no fallacies found" in response.lower():
            return []

        return self._parse_fallacy_response(response)

    def _parse_fallacy_response(self, response: str) -> List[Fallacy]:
        """Parse the AI response for fallacies."""
        lines = response.strip().split('\n')
        fallacies = []
        current_fallacy = {}

        for line in lines:
            line = line.strip()
            if not line:
                if current_fallacy:
                    fallacies.append(Fallacy(**current_fallacy))
                    current_fallacy = {}
                continue

            if line.startswith("Fallacy:"):
                if current_fallacy and "name" in current_fallacy and "text" in current_fallacy:
                    fallacies.append(Fallacy(**current_fallacy))
                # Reset with defaults
                current_fallacy = {
                    "name": line.replace("Fallacy:", "").strip(),
                    "description": "",
                    "text": "",
                    "explanation": ""
                }
            elif line.startswith("Text:"):
                current_fallacy["text"] = line.replace("Text:", "").strip()
            elif line.startswith("Explanation:"):
                explanation = line.replace("Explanation:", "").strip()
                current_fallacy["explanation"] = explanation
                current_fallacy["description"] = explanation # Use explanation as description for now

        if current_fallacy and "name" in current_fallacy and "text" in current_fallacy:
            fallacies.append(Fallacy(**current_fallacy))

        return fallacies

    def _evaluate_strength(self, text: str, structure: Dict[str, Any], fallacies: List[Fallacy]) -> Dict[str, Any]:
        """Evaluate overall argument strength and generate suggestions."""
        prompt = (
            "Evaluate the overall strength of the argument in the following text on a scale of 1-10.\n"
            "Consider the clarity of the thesis, the strength of supporting claims, and the presence of any logical fallacies.\n"
            "Provide a brief critique and 3 specific suggestions for improvement.\n\n"
            "Format:\n"
            "Score: [1-10]\n"
            "Critique: [One paragraph critique]\n"
            "Suggestions:\n"
            "1. [Suggestion 1]\n"
            "2. [Suggestion 2]\n"
            "3. [Suggestion 3]\n\n"
            f"Text:\n{text}"
        )

        success, response, _ = self.model.call(prompt)
        if not success:
            return {"score": 0.0, "critique": "Could not evaluate.", "suggestions": []}

        return self._parse_evaluation_response(response)

    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response for evaluation."""
        lines = response.strip().split('\n')
        score = 0.0
        critique = ""
        suggestions = []
        in_suggestions = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("Score:"):
                try:
                    score_str = line.replace("Score:", "").strip().split("/")[0] # Handle "8/10"
                    score = float(score_str)
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse score from: {line}")
                    score = 0.0
            elif line.startswith("Critique:"):
                critique = line.replace("Critique:", "").strip()
                in_suggestions = False
            elif line.startswith("Suggestions:"):
                in_suggestions = True
            elif in_suggestions and (line[0].isdigit() or line.startswith("-")):
                # Remove numbering like "1. " or "- "
                suggestion = line.lstrip("0123456789.- ").strip()
                suggestions.append(suggestion)
            elif not in_suggestions and not line.startswith("Score:"):
                # Append to critique if multiline
                if critique:
                    critique += " " + line

        return {"score": score, "critique": critique, "suggestions": suggestions}
