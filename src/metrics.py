"""Metrics collection and statistics."""

from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class MetricsCollector:
    """Collects and computes metrics for experiments."""

    # Response tracking
    responses: List[str] = field(default_factory=list)
    unique_responses: set = field(default_factory=set)
    duplicate_responses: List[str] = field(default_factory=list)

    # Timing
    response_times: List[float] = field(default_factory=list)

    # Word counts
    word_counts: List[int] = field(default_factory=list)

    # Error tracking
    error_count: int = 0
    total_attempts: int = 0

    def record_response(
        self,
        response: str,
        response_time: float,
        is_error: bool = False
    ) -> None:
        """
        Record a response and its metrics.

        Args:
            response: The model's response text
            response_time: Time taken for the response (seconds)
            is_error: Whether this was an error response
        """
        self.total_attempts += 1

        if is_error:
            self.error_count += 1
            return

        # Track response
        if response in self.unique_responses:
            self.duplicate_responses.append(response)
        else:
            self.unique_responses.add(response)
            self.responses.append(response)

        # Track timing
        self.response_times.append(response_time)

        # Track word count
        word_count = len(response.split())
        self.word_counts.append(word_count)

    @property
    def duplicate_count(self) -> int:
        """Number of duplicate responses."""
        return len(self.duplicate_responses)

    @property
    def unique_count(self) -> int:
        """Number of unique responses."""
        return len(self.unique_responses)

    @property
    def success_count(self) -> int:
        """Number of successful responses."""
        return len(self.responses)

    @property
    def uniqueness_rate(self) -> float:
        """Percentage of unique responses (0-100)."""
        if self.success_count == 0:
            return 0.0
        return (self.unique_count / self.success_count) * 100

    @property
    def avg_response_time(self) -> float:
        """Average response time in seconds."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    @property
    def min_response_time(self) -> float:
        """Minimum response time in seconds."""
        return min(self.response_times) if self.response_times else 0.0

    @property
    def max_response_time(self) -> float:
        """Maximum response time in seconds."""
        return max(self.response_times) if self.response_times else 0.0

    @property
    def avg_word_count(self) -> float:
        """Average word count in responses."""
        if not self.word_counts:
            return 0.0
        return sum(self.word_counts) / len(self.word_counts)

    @property
    def min_word_count(self) -> int:
        """Minimum word count in responses."""
        return min(self.word_counts) if self.word_counts else 0

    @property
    def max_word_count(self) -> int:
        """Maximum word count in responses."""
        return max(self.word_counts) if self.word_counts else 0

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.

        Returns:
            Dictionary with all computed metrics
        """
        return {
            'total_attempts': self.total_attempts,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'unique_count': self.unique_count,
            'duplicate_count': self.duplicate_count,
            'uniqueness_rate': round(self.uniqueness_rate, 2),
            'response_time': {
                'min': round(self.min_response_time, 2),
                'max': round(self.max_response_time, 2),
                'avg': round(self.avg_response_time, 2),
            },
            'word_count': {
                'min': self.min_word_count,
                'max': self.max_word_count,
                'avg': round(self.avg_word_count, 1),
            }
        }

    def print_summary(self, model_name: str = None) -> None:
        """
        Print a formatted summary of metrics.

        Args:
            model_name: Optional model name to include in summary
        """
        print("\n" + "=" * 80)
        print("METRICS SUMMARY")
        print("=" * 80)

        if model_name:
            print(f"Model: {model_name}")

        summary = self.get_summary()

        print(f"\nAttempts:")
        print(f"  Total: {summary['total_attempts']}")
        print(f"  Successful: {summary['success_count']}")
        print(f"  Errors: {summary['error_count']}")

        print(f"\nUniqueness:")
        print(f"  Unique responses: {summary['unique_count']}")
        print(f"  Duplicate responses: {summary['duplicate_count']}")
        print(f"  Uniqueness rate: {summary['uniqueness_rate']}%")

        if summary['success_count'] > 0:
            print(f"\nResponse Time (seconds):")
            print(f"  Min: {summary['response_time']['min']}")
            print(f"  Max: {summary['response_time']['max']}")
            print(f"  Avg: {summary['response_time']['avg']}")

            print(f"\nWord Count:")
            print(f"  Min: {summary['word_count']['min']}")
            print(f"  Max: {summary['word_count']['max']}")
            print(f"  Avg: {summary['word_count']['avg']}")

        print("=" * 80)

    def reset(self) -> None:
        """Reset all metrics."""
        self.responses.clear()
        self.unique_responses.clear()
        self.duplicate_responses.clear()
        self.response_times.clear()
        self.word_counts.clear()
        self.error_count = 0
        self.total_attempts = 0
