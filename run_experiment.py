#!/usr/bin/env python3
"""
AI Essay Experiment Runner

Command-line interface for running AI essay experiments.
"""

import argparse
import sys
import os
from pathlib import Path
import yaml

from src.models.openrouter import OpenRouterModel
from src.experiment import (
    UniquenessExperiment,
    EssayExperiment,
    TopicClassificationExperiment
)


def load_config(config_file: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"WARNING: Config file {config_file} not found. Using defaults.")
        return {}
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}")
        sys.exit(1)


def run_batch1(args, config):
    """Run batch1 uniqueness experiment."""
    # Get configuration
    exp_config = config.get('experiments', {}).get('batch1', {})
    defaults = config.get('defaults', {})

    # Determine prompt
    if args.prompt:
        prompt = args.prompt
    elif args.prompt_file:
        with open(args.prompt_file, 'r') as f:
            prompt = f.read()
    else:
        prompt = exp_config.get('default_prompt', "How many Rs are in the word strawberry?")

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path(exp_config.get('output_dir', 'results/batch1'))

    # Create model
    model = OpenRouterModel(
        model_name=args.model,
        max_tokens=args.max_tokens or defaults.get('max_tokens', 1000),
        temperature=args.temperature if args.temperature is not None else defaults.get('temperature', 1.0),
        retry_limit=args.retry_limit or defaults.get('retry_limit', 25)
    )

    # Create and run experiment
    experiment = UniquenessExperiment(
        model=model,
        prompt=prompt,
        num_cycles=args.cycles or defaults.get('cycles', 100),
        output_dir=output_dir
    )

    experiment.run()


def run_batch2(args, config):
    """Run batch2 essay generation experiment."""
    # Get configuration
    exp_config = config.get('experiments', {}).get('batch2', {})
    defaults = config.get('defaults', {})

    # Determine essay prompt
    if args.prompt:
        essay_prompt = args.prompt
    elif args.prompt_file:
        with open(args.prompt_file, 'r') as f:
            essay_prompt = f.read()
    else:
        essay_prompt = exp_config.get('essay_prompt', "Write an essay")

    # Determine thesis prompt
    thesis_prompt = args.thesis_prompt or exp_config.get(
        'thesis_prompt',
        "For the below essay, pull out a quote that exemplifies the paper's thesis."
    )

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path(exp_config.get('output_dir', 'results/batch2'))

    # Create model
    model = OpenRouterModel(
        model_name=args.model,
        max_tokens=args.max_tokens or defaults.get('max_tokens', 1000),
        temperature=args.temperature if args.temperature is not None else defaults.get('temperature', 1.0),
        retry_limit=args.retry_limit or defaults.get('retry_limit', 25)
    )

    # Create and run experiment
    experiment = EssayExperiment(
        model=model,
        essay_prompt=essay_prompt,
        thesis_prompt=thesis_prompt,
        num_cycles=args.cycles or defaults.get('cycles', 100),
        output_dir=output_dir
    )

    experiment.run()


def run_batch5(args, config):
    """Run batch5 topic classification experiment."""
    # Get configuration
    exp_config = config.get('experiments', {}).get('batch5', {})
    defaults = config.get('defaults', {})

    # Determine essay file
    if not args.essay_file:
        essay_file = exp_config.get('essay_file')
        if not essay_file:
            print("ERROR: --essay-file required for batch5")
            sys.exit(1)
    else:
        essay_file = args.essay_file

    # Determine topic prompt
    topic_prompt = args.topic_prompt or exp_config.get(
        'topic_prompt',
        "In one or two words state the topic of the below essay."
    )

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path(exp_config.get('output_dir', 'results/batch5'))

    # Create model
    model = OpenRouterModel(
        model_name=args.model,
        max_tokens=args.max_tokens or defaults.get('max_tokens', 1000),
        temperature=args.temperature if args.temperature is not None else defaults.get('temperature', 1.0),
        retry_limit=args.retry_limit or defaults.get('retry_limit', 25)
    )

    # Create and run experiment
    experiment = TopicClassificationExperiment(
        model=model,
        essay_file=Path(essay_file),
        topic_prompt=topic_prompt,
        num_cycles=args.cycles or defaults.get('cycles', 100),
        output_dir=output_dir
    )

    experiment.run()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run AI Essay Experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Batch 1: Test response uniqueness
  python run_experiment.py batch1 --model claude-sonnet-4 --cycles 100

  # Batch 2: Generate essays and extract theses
  python run_experiment.py batch2 --model gpt-4o --prompt-file prompt.txt

  # Batch 5: Classify essay topics
  python run_experiment.py batch5 --model gemini-2.5-flash --essay-file essays.txt
        """
    )

    parser.add_argument(
        'experiment',
        choices=['batch1', 'batch2', 'batch5'],
        help='Experiment type to run'
    )

    parser.add_argument(
        '--model',
        required=False,
        help='AI model to use (overrides OPENROUTER_MODEL env var)'
    )

    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )

    # Common options
    parser.add_argument('--cycles', type=int, help='Number of cycles to run')
    parser.add_argument('--temperature', type=float, help='Sampling temperature (0.0-2.0)')
    parser.add_argument('--max-tokens', type=int, help='Maximum tokens in response')
    parser.add_argument('--retry-limit', type=int, help='Maximum retry attempts')
    parser.add_argument('--output-dir', help='Output directory for results')

    # Batch 1 options
    parser.add_argument('--prompt', help='Prompt text (batch1)')
    parser.add_argument('--prompt-file', help='File containing prompt (batch1, batch2)')

    # Batch 2 options
    parser.add_argument('--thesis-prompt', help='Thesis extraction prompt (batch2)')

    # Batch 5 options
    parser.add_argument('--essay-file', help='File containing essays (batch5)')
    parser.add_argument('--topic-prompt', help='Topic classification prompt (batch5)')

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Determine model to use
    model_name = args.model or os.getenv('OPENROUTER_MODEL')
    if not model_name:
        print("ERROR: No model specified. Use --model or set OPENROUTER_MODEL environment variable.")
        sys.exit(1)
    
    # Update args with resolved model name for downstream functions
    args.model = model_name

    # Run appropriate experiment
    if args.experiment == 'batch1':
        run_batch1(args, config)
    elif args.experiment == 'batch2':
        run_batch2(args, config)
    elif args.experiment == 'batch5':
        run_batch5(args, config)


if __name__ == '__main__':
    main()
