"""Main experiment runner for AI testing."""

import time
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from .models.base import AIModel
from .metrics import MetricsCollector
from .utils import print_formatted, write_to_file, extract_essay, ensure_dir, clear_file

# Load environment variables
load_dotenv()


class ExperimentRunner:
    """Base class for running AI experiments."""

    def __init__(
        self,
        model: AIModel,
        num_cycles: int,
        output_dir: Path = Path(".")
    ):
        """
        Initialize experiment runner.

        Args:
            model: AIModel instance to use
            num_cycles: Number of experiment cycles to run
            output_dir: Directory for output files
        """
        self.model = model
        self.num_cycles = num_cycles
        self.output_dir = Path(output_dir)
        self.metrics = MetricsCollector()

        # Ensure output directory exists
        ensure_dir(self.output_dir)

    def run(self) -> None:
        """Run the experiment. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement run()")


class UniquenessExperiment(ExperimentRunner):
    """Experiment to test response uniqueness."""

    def __init__(
        self,
        model: AIModel,
        prompt: str,
        num_cycles: int,
        output_dir: Path = Path(".")
    ):
        """
        Initialize uniqueness experiment.

        Args:
            model: AIModel instance to use
            prompt: The prompt to test
            num_cycles: Number of test cycles
            output_dir: Directory for output files
        """
        super().__init__(model, num_cycles, output_dir)
        self.prompt = prompt

    def run(self) -> None:
        """Run uniqueness testing experiment."""
        print("=" * 80)
        print("RESPONSE UNIQUENESS EXPERIMENT")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"Cycles: {self.num_cycles}")
        print(f"\nPrompt:")
        print_formatted(self.prompt)
        print("-" * 80)
        print()

        for cycle in range(self.num_cycles):
            retry_count = 0

            while retry_count < self.model.retry_limit:
                start_time = time.time()

                success, response, error_text = self.model.call(self.prompt)

                elapsed_time = time.time() - start_time

                if not success:
                    print(f"\n{error_text}")
                    retry_count += 1
                    self.metrics.record_response("", elapsed_time, is_error=True)
                    continue

                # Record successful response
                self.metrics.record_response(response, elapsed_time)

                # Display progress
                print(
                    f"\nCycle: {cycle + 1}/{self.num_cycles} | "
                    f"Duplicates: {self.metrics.duplicate_count} | "
                    f"Time: {elapsed_time:.2f}s\n"
                )
                print_formatted(response)
                print()

                break  # Success, move to next cycle

            else:
                # Retry limit exceeded
                print(f"\nERROR: Retry limit exceeded ({self.model.retry_limit})")
                sys.exit(1)

        # Print final report
        self.print_report()

    def print_report(self) -> None:
        """Print final experiment report."""
        print("\n" + "=" * 80)
        print("FINAL REPORT")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"\nPrompt:")
        print_formatted(self.prompt)

        # Sample unique responses
        if self.metrics.unique_count >= 5:
            print("\nFirst 5 Unique Responses:")
            print("-" * 80)
            for i in range(5):
                print(f"{i+1}. {self.metrics.responses[i]}")

        # Print metrics summary
        self.metrics.print_summary()

        # Duplicates detail
        if self.metrics.duplicate_count > 0:
            print("\n" + "-" * 80)
            print(f"DUPLICATE RESPONSES ({self.metrics.duplicate_count} total)")
            print("-" * 80)
            for i, dup in enumerate(self.metrics.duplicate_responses, 1):
                print(f"{i}. {dup}")


class EssayExperiment(ExperimentRunner):
    """Experiment to generate essays and extract theses."""

    def __init__(
        self,
        model: AIModel,
        essay_prompt: str,
        thesis_prompt: str,
        num_cycles: int,
        output_dir: Path = Path(".")
    ):
        """
        Initialize essay experiment.

        Args:
            model: AIModel instance to use
            essay_prompt: Prompt for essay generation
            thesis_prompt: Prompt for thesis extraction
            num_cycles: Number of essays to generate
            output_dir: Directory for output files
        """
        super().__init__(model, num_cycles, output_dir)
        self.essay_prompt = essay_prompt
        self.thesis_prompt = thesis_prompt

        # Output files
        self.essay_file = self.output_dir / "essay.txt"
        self.thesis_file = self.output_dir / "thesis.txt"

    def run(self) -> None:
        """Run essay generation experiment."""
        print("=" * 80)
        print("ESSAY GENERATION & THESIS EXTRACTION EXPERIMENT")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"Cycles: {self.num_cycles}")
        print(f"Output directory: {self.output_dir}")
        print(f"\nEssay Prompt:")
        print_formatted(self.essay_prompt)
        print(f"\nThesis Prompt:")
        print_formatted(self.thesis_prompt)
        print("-" * 80)
        print()

        # Clear output files
        clear_file(self.essay_file)
        clear_file(self.thesis_file)

        for cycle in range(self.num_cycles):
            print(f"\n{'#' * 80}")
            print(f"CYCLE {cycle + 1}/{self.num_cycles}")
            print('#' * 80)

            # Step 1: Generate essay
            essay_text = self._generate_essay(cycle)
            if essay_text is None:
                sys.exit(1)

            # Step 2: Extract thesis
            thesis_text = self._extract_thesis(cycle, essay_text)
            if thesis_text is None:
                sys.exit(1)

        # Print final report
        self.print_report()

    def _generate_essay(self, cycle: int) -> Optional[str]:
        """Generate an essay."""
        retry_count = 0

        while retry_count < self.model.retry_limit:
            success, response, error_text = self.model.call(self.essay_prompt)

            if not success:
                print(f"\n{error_text}")
                retry_count += 1
                self.metrics.error_count += 1
                continue

            # Display and save essay
            print(f"\n{'=' * 80}")
            print(f"ESSAY #{cycle + 1}")
            print('=' * 80)
            print_formatted(response)
            print()

            write_to_file(
                self.essay_file,
                f"\n\n\n******** Essay number: {cycle + 1} ************\n\n{response}"
            )

            return response

        print(f"\nERROR: Failed to generate essay after {self.model.retry_limit} retries")
        return None

    def _extract_thesis(self, cycle: int, essay_text: str) -> Optional[str]:
        """Extract thesis from essay."""
        retry_count = 0
        full_prompt = f"{self.thesis_prompt}\n\n{essay_text}"

        while retry_count < self.model.retry_limit:
            success, response, error_text = self.model.call(full_prompt)

            if not success:
                print(f"\n{error_text}")
                retry_count += 1
                self.metrics.error_count += 1
                continue

            # Display and save thesis
            print(f"\n{'-' * 80}")
            print(f"THESIS #{cycle + 1}")
            print('-' * 80)
            print_formatted(response)
            print()

            write_to_file(
                self.thesis_file,
                f"\n\n******** Thesis number: {cycle + 1} ************\n\n{response}"
            )

            return response

        print(f"\nERROR: Failed to extract thesis after {self.model.retry_limit} retries")
        return None

    def print_report(self) -> None:
        """Print final experiment report."""
        print("\n" + "=" * 80)
        print("FINAL REPORT")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"Total cycles: {self.num_cycles}")
        print(f"API errors: {self.metrics.error_count}")
        print(f"\nOutput files:")
        print(f"  Essays: {self.essay_file}")
        print(f"  Theses: {self.thesis_file}")
        print("=" * 80)


class TopicClassificationExperiment(ExperimentRunner):
    """Experiment to classify essay topics."""

    def __init__(
        self,
        model: AIModel,
        essay_file: Path,
        topic_prompt: str,
        num_cycles: int,
        output_dir: Path = Path(".")
    ):
        """
        Initialize topic classification experiment.

        Args:
            model: AIModel instance to use
            essay_file: File containing pre-generated essays
            topic_prompt: Prompt for topic classification
            num_cycles: Number of essays to classify
            output_dir: Directory for output files
        """
        super().__init__(model, num_cycles, output_dir)
        self.essay_file = Path(essay_file)
        self.topic_prompt = topic_prompt

        # Validate essay file exists
        if not self.essay_file.exists():
            raise FileNotFoundError(f"Essay file not found: {self.essay_file}")

        # Output file
        self.topic_file = self.output_dir / "topic.txt"

    def run(self) -> None:
        """Run topic classification experiment."""
        print("=" * 80)
        print("ESSAY TOPIC CLASSIFICATION EXPERIMENT")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"Cycles: {self.num_cycles}")
        print(f"Essay file: {self.essay_file}")
        print(f"Output directory: {self.output_dir}")
        print(f"\nTopic Classification Prompt:")
        print_formatted(self.topic_prompt)
        print("-" * 80)
        print()

        # Clear output file
        clear_file(self.topic_file)

        for cycle in range(self.num_cycles):
            print(f"\n{'#' * 80}")
            print(f"CYCLE {cycle + 1}/{self.num_cycles}")
            print('#' * 80)

            # Extract essay
            essay_text = extract_essay(self.essay_file, cycle + 1)
            if essay_text is None:
                print(f"\nERROR: Essay #{cycle + 1} not found in {self.essay_file}")
                sys.exit(1)

            # Classify topic
            topic_text = self._classify_topic(cycle, essay_text)
            if topic_text is None:
                sys.exit(1)

        # Print final report
        self.print_report()

    def _classify_topic(self, cycle: int, essay_text: str) -> Optional[str]:
        """Classify essay topic."""
        retry_count = 0
        full_prompt = f"{self.topic_prompt}\n\n{essay_text}"

        while retry_count < self.model.retry_limit:
            success, response, error_text = self.model.call(full_prompt)

            if not success:
                print(f"\n{error_text}")
                retry_count += 1
                self.metrics.error_count += 1
                continue

            # Display and save topic
            print(f"\n{'=' * 80}")
            print(f"ESSAY #{cycle + 1} - TOPIC CLASSIFICATION")
            print('=' * 80)
            print("Topic:")
            print_formatted(response)
            print()

            write_to_file(
                self.topic_file,
                f"\n\n******** Topic number: {cycle + 1} ************\n\n{response}"
            )

            return response

        print(f"\nERROR: Failed to classify topic after {self.model.retry_limit} retries")
        return None

    def print_report(self) -> None:
        """Print final experiment report."""
        print("\n" + "=" * 80)
        print("FINAL REPORT")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"Total cycles: {self.num_cycles}")
        print(f"API errors: {self.metrics.error_count}")
        print(f"\nOutput file:")
        print(f"  Topics: {self.topic_file}")
        print("=" * 80)
