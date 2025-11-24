"""Grammar & Clarity Optimizer."""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .models.base import AIModel

logger = logging.getLogger(__name__)


@dataclass
class OptimizationIssue:
    """A single grammar or clarity issue."""

    type: str  # "grammar", "clarity", "style", "voice"
    severity: str  # "error", "warning", "suggestion"
    message: str
    original_text: str
    suggested_text: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class ReadabilityMetrics:
    """Readability and style metrics."""

    flesch_reading_ease: float  # 0-100, higher is easier
    flesch_kincaid_grade: float  # US grade level
    avg_sentence_length: float
    avg_word_length: float
    passive_voice_percentage: float
    total_sentences: int
    total_words: int
    complex_words: int


@dataclass
class OptimizationResult:
    """Result of optimization analysis."""

    issues: List[OptimizationIssue]
    metrics: ReadabilityMetrics
    optimized_text: Optional[str] = None
    improvements_applied: int = 0


class GrammarOptimizer:
    """Advanced grammar, clarity, and style optimizer."""

    # Common clichés to detect
    CLICHES = [
        "at the end of the day",
        "think outside the box",
        "low-hanging fruit",
        "paradigm shift",
        "circle back",
        "touch base",
        "move the needle",
        "on the same page",
        "game changer",
        "level the playing field",
        "it goes without saying",
        "needless to say",
        "in today's society",
        "since the dawn of time",
        "in conclusion",
    ]

    # Wordy phrases to simplify
    WORDY_PHRASES = {
        "in order to": "to",
        "due to the fact that": "because",
        "at this point in time": "now",
        "in spite of the fact that": "although",
        "for the purpose of": "to",
        "in the event that": "if",
        "on the occasion of": "when",
        "with regard to": "regarding",
        "in the process of": "during",
        "by means of": "by",
        "in the amount of": "for",
        "at the present time": "now",
        "during the course of": "during",
        "a majority of": "most",
        "a number of": "several",
    }

    # Weak verbs to flag
    WEAK_VERBS = ["is", "are", "was", "were", "be", "been", "being", "get", "got", "have", "has", "had"]

    def __init__(self, model: Optional[AIModel] = None):
        """
        Initialize the optimizer.

        Args:
            model: Optional AI model for intelligent suggestions.
        """
        self.model = model

    def optimize(
        self,
        text: str,
        target_grade_level: Optional[float] = None,
        prefer_active_voice: bool = True,
        apply_fixes: bool = False,
    ) -> OptimizationResult:
        """
        Analyze and optimize text for grammar, clarity, and style.

        Args:
            text: Text to optimize.
            target_grade_level: Target Flesch-Kincaid grade level.
            prefer_active_voice: Flag passive voice usage.
            apply_fixes: If True, apply automatic fixes.

        Returns:
            OptimizationResult with issues and metrics.
        """
        issues: List[OptimizationIssue] = []

        # Calculate readability metrics
        metrics = self._calculate_readability(text)

        # Detect various issues
        issues.extend(self._detect_cliches(text))
        issues.extend(self._detect_wordy_phrases(text))
        issues.extend(self._detect_weak_verbs(text))

        if prefer_active_voice:
            issues.extend(self._detect_passive_voice(text))

        # Check grade level
        if target_grade_level and metrics.flesch_kincaid_grade > target_grade_level:
            issues.append(
                OptimizationIssue(
                    type="clarity",
                    severity="warning",
                    message=f"Reading level ({metrics.flesch_kincaid_grade:.1f}) exceeds target ({target_grade_level})",
                    original_text="",
                )
            )

        # Use AI for advanced grammar and clarity analysis
        if self.model:
            ai_issues = self._ai_grammar_check(text)
            issues.extend(ai_issues)

        # Apply automatic fixes if requested
        optimized_text = None
        improvements_applied = 0

        if apply_fixes:
            optimized_text, improvements_applied = self._apply_fixes(text, issues)

        return OptimizationResult(
            issues=issues,
            metrics=metrics,
            optimized_text=optimized_text,
            improvements_applied=improvements_applied,
        )

    def _calculate_readability(self, text: str) -> ReadabilityMetrics:
        """Calculate readability metrics."""
        try:
            import textstat
        except ImportError:
            logger.warning("textstat not installed, using approximate metrics")
            return self._approximate_readability(text)

        # Use textstat for accurate metrics
        flesch_ease = textstat.flesch_reading_ease(text)
        flesch_grade = textstat.flesch_kincaid_grade(text)
        avg_sentence_length = textstat.words_per_sentence(text)

        sentences = self._split_sentences(text)
        words = text.split()

        # Calculate additional metrics
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        complex_words = sum(1 for w in words if len(w) > 10)
        passive_pct = self._calculate_passive_percentage(text)

        return ReadabilityMetrics(
            flesch_reading_ease=max(0, min(100, flesch_ease)),
            flesch_kincaid_grade=max(0, flesch_grade),
            avg_sentence_length=avg_sentence_length,
            avg_word_length=avg_word_length,
            passive_voice_percentage=passive_pct,
            total_sentences=len(sentences),
            total_words=len(words),
            complex_words=complex_words,
        )

    def _approximate_readability(self, text: str) -> ReadabilityMetrics:
        """Approximate readability metrics without textstat."""
        sentences = self._split_sentences(text)
        words = text.split()

        if not sentences or not words:
            return ReadabilityMetrics(
                flesch_reading_ease=0,
                flesch_kincaid_grade=0,
                avg_sentence_length=0,
                avg_word_length=0,
                passive_voice_percentage=0,
                total_sentences=0,
                total_words=0,
                complex_words=0,
            )

        total_syllables = sum(self._count_syllables(w) for w in words)
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)

        # Flesch Reading Ease: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        flesch_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)

        # Flesch-Kincaid Grade: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        flesch_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59

        avg_word_length = sum(len(w) for w in words) / len(words)
        complex_words = sum(1 for w in words if len(w) > 10)
        passive_pct = self._calculate_passive_percentage(text)

        return ReadabilityMetrics(
            flesch_reading_ease=max(0, min(100, flesch_ease)),
            flesch_kincaid_grade=max(0, flesch_grade),
            avg_sentence_length=avg_sentence_length,
            avg_word_length=avg_word_length,
            passive_voice_percentage=passive_pct,
            total_sentences=len(sentences),
            total_words=len(words),
            complex_words=complex_words,
        )

    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count for a word."""
        word = word.lower().strip(".,!?;:")
        vowels = "aeiou"
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent 'e'
        if word.endswith("e"):
            syllable_count -= 1

        # Ensure at least one syllable
        return max(1, syllable_count)

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Note: Simple regex-based splitter. May split incorrectly on abbreviations
        like "Dr. Smith" or "U.S.A". This is acceptable for the fallback path since
        textstat provides more accurate sentence detection for readability metrics.
        """
        # Common abbreviations that shouldn't trigger sentence breaks
        # Protect them temporarily
        protected = text
        abbreviations = [
            (r'\bDr\.', 'Dr<DOT>'),
            (r'\bMr\.', 'Mr<DOT>'),
            (r'\bMrs\.', 'Mrs<DOT>'),
            (r'\bMs\.', 'Ms<DOT>'),
            (r'\bProf\.', 'Prof<DOT>'),
            (r'\b([A-Z])\.([A-Z])\.', r'\1<DOT>\2<DOT>'),  # U.S., U.K.
        ]

        for pattern, replacement in abbreviations:
            protected = re.sub(pattern, replacement, protected)

        # Split on sentence terminators followed by whitespace
        sentences = re.split(r'[.!?]+\s+', protected)

        # Restore dots in abbreviations
        sentences = [s.replace('<DOT>', '.').strip() for s in sentences if s.strip()]

        return sentences

    def _calculate_passive_percentage(self, text: str) -> float:
        """Calculate percentage of passive voice usage."""
        sentences = self._split_sentences(text)
        if not sentences:
            return 0.0

        passive_count = 0
        for sentence in sentences:
            if self._is_passive_voice(sentence):
                passive_count += 1

        return (passive_count / len(sentences)) * 100

    def _is_passive_voice(self, sentence: str) -> bool:
        """Detect if a sentence uses passive voice."""
        sentence_lower = sentence.lower()

        # Look for "to be" verb + past participle patterns
        passive_indicators = [
            r'\b(is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\b(is|are|was|were|be|been|being)\s+\w+en\b',
        ]

        for pattern in passive_indicators:
            if re.search(pattern, sentence_lower):
                return True

        return False

    def _detect_cliches(self, text: str) -> List[OptimizationIssue]:
        """Detect clichés in text."""
        issues = []
        text_lower = text.lower()

        for cliche in self.CLICHES:
            if cliche in text_lower:
                issues.append(
                    OptimizationIssue(
                        type="style",
                        severity="suggestion",
                        message=f"Avoid cliché: '{cliche}'",
                        original_text=cliche,
                        suggested_text="[consider rephrasing]",
                    )
                )

        return issues

    def _detect_wordy_phrases(self, text: str) -> List[OptimizationIssue]:
        """Detect wordy phrases that can be simplified."""
        issues = []
        text_lower = text.lower()

        for wordy, concise in self.WORDY_PHRASES.items():
            if wordy in text_lower:
                issues.append(
                    OptimizationIssue(
                        type="clarity",
                        severity="suggestion",
                        message=f"Simplify wordy phrase",
                        original_text=wordy,
                        suggested_text=concise,
                    )
                )

        return issues

    def _detect_weak_verbs(self, text: str) -> List[OptimizationIssue]:
        """Detect weak verbs in text."""
        issues = []
        sentences = self._split_sentences(text)

        for sentence in sentences:
            words = sentence.split()
            weak_verb_count = sum(1 for w in words if w.lower() in self.WEAK_VERBS)

            # Flag sentences with multiple weak verbs
            if weak_verb_count >= 3:
                issues.append(
                    OptimizationIssue(
                        type="style",
                        severity="suggestion",
                        message=f"Consider using stronger verbs (found {weak_verb_count} weak verbs)",
                        original_text=sentence[:50] + "..." if len(sentence) > 50 else sentence,
                    )
                )

        return issues

    def _detect_passive_voice(self, text: str) -> List[OptimizationIssue]:
        """Detect passive voice usage."""
        issues = []
        sentences = self._split_sentences(text)

        for sentence in sentences:
            if self._is_passive_voice(sentence):
                issues.append(
                    OptimizationIssue(
                        type="voice",
                        severity="suggestion",
                        message="Consider using active voice",
                        original_text=sentence[:60] + "..." if len(sentence) > 60 else sentence,
                    )
                )

        return issues

    def _ai_grammar_check(self, text: str) -> List[OptimizationIssue]:
        """Use AI to detect grammar and clarity issues."""
        if not self.model:
            return []

        prompt = (
            "Analyze the following text for grammar, clarity, and style issues. "
            "For each issue, provide:\n"
            "1. The type (grammar/clarity/style)\n"
            "2. A brief description\n"
            "3. The problematic text\n"
            "4. A suggested fix\n\n"
            f"Text:\n{text}\n\n"
            "Format your response as a list of issues."
        )

        success, response, error = self.model.call(prompt)

        if not success or not response.strip():
            logger.warning("AI grammar check failed: %s", error)
            return []

        # Parse AI response into issues
        return self._parse_ai_grammar_response(response)

    def _parse_ai_grammar_response(self, response: str) -> List[OptimizationIssue]:
        """Parse AI grammar check response."""
        issues = []
        lines = response.strip().split('\n')

        current_issue = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_issue:
                    # Create issue from accumulated data
                    issue_type = current_issue.get("type", "grammar")
                    issues.append(
                        OptimizationIssue(
                            type=issue_type,
                            severity="warning",
                            message=current_issue.get("description", "Grammar issue"),
                            original_text=current_issue.get("original", ""),
                            suggested_text=current_issue.get("suggestion", None),
                        )
                    )
                    current_issue = {}
                continue

            # Parse issue fields
            if "type:" in line.lower():
                current_issue["type"] = line.split(":", 1)[1].strip().lower()
            elif "description:" in line.lower() or "issue:" in line.lower():
                current_issue["description"] = line.split(":", 1)[1].strip()
            elif "original:" in line.lower() or "problematic:" in line.lower():
                current_issue["original"] = line.split(":", 1)[1].strip()
            elif "suggestion:" in line.lower() or "fix:" in line.lower():
                current_issue["suggestion"] = line.split(":", 1)[1].strip()

        # Add last issue if exists
        if current_issue:
            issues.append(
                OptimizationIssue(
                    type=current_issue.get("type", "grammar"),
                    severity="warning",
                    message=current_issue.get("description", "Grammar issue"),
                    original_text=current_issue.get("original", ""),
                    suggested_text=current_issue.get("suggestion", None),
                )
            )

        return issues

    def _apply_fixes(self, text: str, issues: List[OptimizationIssue]) -> Tuple[str, int]:
        """
        Apply automatic fixes to text.

        Replaces all occurrences of fixable issues. For multiple instances of the
        same phrase, each will be replaced in the order they appear.
        """
        optimized = text
        count = 0

        # Only apply fixes that have clear suggestions
        for issue in issues:
            if issue.suggested_text and issue.original_text and \
               issue.suggested_text != "[consider rephrasing]" and \
               issue.suggested_text != "[rewrite in active voice]":
                # Skip if we've already applied a fix for this exact text (case-insensitive)
                pattern = re.compile(re.escape(issue.original_text), re.IGNORECASE)
                
                def replace_match(match):
                    original = match.group(0)
                    replacement = issue.suggested_text
                    
                    # Check for capitalization (Title case or Sentence case)
                    if original and original[0].isupper() and replacement:
                        replacement = replacement[0].upper() + replacement[1:]
                    
                    return replacement

                # Replace all occurrences with case preservation
                optimized, n = pattern.subn(replace_match, optimized)
                count += n

        return optimized, count
