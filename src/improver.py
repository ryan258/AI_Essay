"""Essay Improvement Engine."""

import logging
import re
import statistics
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from .analyzer import EssayAnalyzer
from .models.base import AIModel

logger = logging.getLogger(__name__)


@dataclass
class ImprovementScores:
    """Scores for a single iteration."""

    clarity: float
    grammar: float
    argument_strength: float
    overall: float


@dataclass
class ImprovementStep:
    """Before/after data for one improvement cycle."""

    iteration: int
    before_text: str
    after_text: str
    scores_before: ImprovementScores
    scores_after: ImprovementScores
    applied_model: Optional[str] = None


@dataclass
class ImprovementResult:
    """Full result of an improvement run."""

    iterations: List[ImprovementStep]
    final_text: str
    final_scores: ImprovementScores
    reached_target: bool
    target_score: float


class EssayImprover:
    """Iteratively improves an essay."""

    def __init__(self, model: Optional[AIModel] = None):
        """
        Initialize the improver.

        Args:
            model: Optional AI model used to rewrite paragraphs.
        """
        self.model = model
        self.analyzer = EssayAnalyzer()

    def improve(
        self,
        essay_text: str,
        cycles: int = 3,
        target_score: float = 85.0,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> ImprovementResult:
        """
        Improve an essay iteratively.

        Args:
            essay_text: Raw essay text.
            cycles: Maximum number of improvement cycles.
            target_score: Stop early when overall score meets/exceeds this value.
            progress_callback: Optional callable to report progress per cycle.

        Returns:
            ImprovementResult with iteration history and final text.
        """
        iterations: List[ImprovementStep] = []
        max_cycles = max(1, cycles)
        consecutive_no_improvement = 0

        current_text = essay_text.strip()
        current_scores = self._score_text(current_text)

        # If we already meet the target, skip rewriting
        if current_scores.overall >= target_score:
            return ImprovementResult(
                iterations=[],
                final_text=current_text,
                final_scores=current_scores,
                reached_target=True,
                target_score=target_score,
            )

        for i in range(1, max_cycles + 1):
            if progress_callback:
                progress_callback(i, max_cycles)

            before_scores = self._score_text(current_text)
            revised_text, used_model = self._apply_improvement(current_text)
            after_scores = self._score_text(revised_text)

            iterations.append(
                ImprovementStep(
                    iteration=i,
                    before_text=current_text,
                    after_text=revised_text,
                    scores_before=before_scores,
                    scores_after=after_scores,
                    applied_model=used_model,
                )
            )

            current_text = revised_text
            current_scores = after_scores

            if current_scores.overall >= target_score:
                break

            # Stop if no measurable improvement for two consecutive cycles
            if after_scores.overall <= before_scores.overall:
                consecutive_no_improvement += 1
            else:
                consecutive_no_improvement = 0

            if consecutive_no_improvement >= 2:
                break

        return ImprovementResult(
            iterations=iterations,
            final_text=current_text,
            final_scores=current_scores,
            reached_target=current_scores.overall >= target_score,
            target_score=target_score,
        )

    def _apply_improvement(self, text: str) -> Tuple[str, Optional[str]]:
        """
        Apply a single improvement pass.

        Prefers the configured AI model, but falls back to deterministic cleanup
        to keep the MVP usable offline.
        """
        if self.model:
            prompt = (
                "Improve the following essay for clarity, grammar, and argument strength. "
                "Preserve the original meaning and paragraph boundaries. "
                "Return ONLY the improved essay text.\n\n"
                f"{text}"
            )
            success, response, error = self.model.call(prompt)
            if success and response.strip():
                return response.strip(), self.model.model_id
            logger.warning("Model improvement failed, using heuristic fallback: %s", error)

        return self._heuristic_improvement(text), None

    def _score_text(self, text: str) -> ImprovementScores:
        """Compute clarity/grammar/argument scores for a text."""
        clarity = self._clarity_score(text)
        grammar = self._grammar_score(text)
        structure_score = self.analyzer.analyze(text).overall_score

        # Weighted blend favors structure and clarity
        overall = round((clarity * 0.35) + (grammar * 0.25) + (structure_score * 0.40), 1)
        return ImprovementScores(
            clarity=round(clarity, 1),
            grammar=round(grammar, 1),
            argument_strength=round(structure_score, 1),
            overall=overall,
        )

    def _clarity_score(self, text: str) -> float:
        """Score clarity based on sentence length and consistency."""
        sentences = self._split_sentences(text)
        if not sentences:
            return 40.0

        lengths = [len(s.split()) for s in sentences if s.split()]
        if not lengths:
            return 40.0

        avg_len = sum(lengths) / len(lengths)
        variability = statistics.pvariance(lengths) if len(lengths) > 1 else 0.0

        # Ideal range ~15-22 words per sentence with low variance
        target_min, target_max = 15, 22
        if target_min <= avg_len <= target_max:
            length_penalty = 0.0
        else:
            target = target_min if avg_len < target_min else target_max
            length_penalty = abs(avg_len - target) * 2.0

        variance_penalty = min(20.0, variability / 3)

        return self._clamp(100.0 - length_penalty - variance_penalty, 5.0, 100.0)

    def _grammar_score(self, text: str) -> float:
        """Score grammar using simple heuristics (MVP, not exhaustive)."""
        sentences = self._split_sentences(text)
        if not sentences:
            return 45.0

        penalty = 0.0
        penalty += text.count("  ") * 3  # Double-space issues

        for sentence in sentences:
            if not sentence:
                continue
            if not sentence[0].isupper():
                penalty += 4
            if sentence[-1] not in ".!?":
                penalty += 4

        return self._clamp(98.0 - penalty, 5.0, 100.0)

    def _heuristic_improvement(self, text: str) -> str:
        """Deterministic cleanup pass to improve readability."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return text.strip()

        improved_paragraphs: List[str] = []

        for para in paragraphs:
            sentences = self._split_sentences(para)
            cleaned: List[str] = []

            for sentence in sentences:
                sentence = re.sub(r"\s+", " ", sentence.strip())
                if not sentence:
                    continue

                words = sentence.split()

                # Break up run-on sentences
                if len(words) > 30:
                    midpoint = len(words) // 2
                    split_sentences = [
                        " ".join(words[:midpoint]) + ".",
                        " ".join(words[midpoint:]) + ".",
                    ]
                else:
                    split_sentences = [sentence]

                for chunk in split_sentences:
                    chunk = chunk.strip()
                    if not chunk:
                        continue

                    if chunk[-1] not in ".!?":
                        chunk += "."
                    chunk = chunk[0].upper() + chunk[1:] if chunk else chunk

                    cleaned.append(chunk)

            improved_para = " ".join(cleaned)
            if improved_para:
                improved_paragraphs.append(improved_para)

        return "\n\n".join(improved_paragraphs) if improved_paragraphs else text.strip()

    def _split_sentences(self, text: str) -> List[str]:
        """Lightweight sentence splitter tolerant of missing punctuation."""
        normalized = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
        if not normalized:
            return []

        sentences = re.split(r"(?<=[.!?])\s+", normalized)
        sentences = [s.strip() for s in sentences if s.strip()]

        # If no punctuation was found, treat the whole thing as one sentence
        if not sentences and normalized:
            sentences = [normalized]

        return sentences

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        """Clamp a numeric value."""
        return max(min_value, min(value, max_value))
