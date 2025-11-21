# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Essay is a research project exploring AI model responses, specifically focused on essay generation, classification, and response uniqueness testing. The project has been refactored to use OpenRouter for unified access to multiple AI models (Claude, GPT, Gemini, and Grok) through a single API.

The project was created by Stephen Witty in collaboration with Hannah Witty.

## Repository Structure

```
AI_Essay/
├── batch1_unified.py       # Response uniqueness testing
├── batch2_unified.py       # Essay generation + thesis extraction
├── batch5_unified.py       # Topic classification
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore rules
├── README.md              # User-facing documentation
├── CLAUDE.md              # This file
├── ROADMAP.md             # Refactoring roadmap
├── examples/
│   └── batch5/            # Example input/output files from batch5
│       ├── claude.py      # Legacy script (reference)
│       ├── essay.txt      # Sample essays
│       └── topic.txt      # Sample topics
└── Source and Results/    # Legacy code (archived)
    ├── claude/
    ├── gpt/
    ├── gemini/
    └── grok/
```

## Key Improvements Over Legacy Code

The refactored scripts eliminate ~85% code duplication by:
1. **Unified API**: All models accessed through OpenRouter instead of 4 separate SDKs
2. **Single codebase**: One script per experiment type instead of 4 (claude.py, gpt.py, gemini.py, grok.py)
3. **Better architecture**: Object-oriented design with proper separation of concerns
4. **CLI interface**: Command-line arguments instead of editing constants
5. **Security**: Environment variables instead of hardcoded API keys
6. **Efficiency**: Reusable API client (not recreated per call)
7. **Data structures**: Sets for O(1) duplicate detection instead of O(n) lists

## Running Experiments

### Setup

1. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

2. Configure API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenRouter API key
   ```

3. Get an OpenRouter API key from https://openrouter.ai/keys

### Batch 1: Response Uniqueness Testing

Tests how often models generate duplicate responses to the same prompt.

```bash
# Basic usage
uv run run_experiment.py batch1 --model anthropic/claude-3-sonnet --cycles 100

# Custom prompt
uv run run_experiment.py batch1 --model openai/gpt-4o --prompt "What color is the sky?" --cycles 50

# Available models
uv run run_experiment.py batch1 --help
```

**Models**: Any OpenRouter model ID (e.g., `anthropic/claude-3-opus`, `openai/gpt-4o`)

**Output**: Prints statistics on duplicates, response times, and word counts

### Batch 2: Essay Generation + Thesis Extraction

Two-stage process: generates essays, then extracts thesis statements.

```bash
# Using a prompt file
uv run run_experiment.py batch2 --model anthropic/claude-3-sonnet --prompt-file examples/batch5/prompt.txt --cycles 100

# Using inline prompt
uv run run_experiment.py batch2 --model openai/gpt-4o --prompt "Write an essay about learning" --cycles 10

# Custom output directory
uv run run_experiment.py batch2 --model google/gemini-flash-1.5 --prompt-file prompt.txt --output-dir results/gemini/
```

**Output files**:
- `essay.txt`: Generated essays
- `thesis.txt`: Extracted thesis statements

### Batch 5: Topic Classification

Reads pre-generated essays and classifies their topics.

```bash
# Classify essays from file
uv run run_experiment.py batch5 --model anthropic/claude-3-sonnet --essay-file examples/batch5/essay.txt --cycles 100

# Custom output location
uv run run_experiment.py batch5 --model openai/gpt-4o --essay-file essays.txt --output-dir results/topics/
```

**Input**: File with essays separated by markers `******** Essay number: N ************`

**Output**: `topic.txt` with classified topics

## Code Architecture

### Unified API Pattern

All scripts use the same architecture:

```python
from openai import OpenAI

# Initialize once (reused across calls)
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Call any model with same interface
completion = client.chat.completions.create(
    model="anthropic/claude-3-sonnet",  # or any other model
    messages=[...],
    max_tokens=1000,
    temperature=1.0
)
```

### Class-Based Design

Each experiment type is a class:

- `UniquenessExperiment`: Batch 1 logic
- `EssayExperiment`: Batch 2 logic
- `TopicClassificationExperiment`: Batch 5 logic

Benefits:
- Encapsulation of state and logic
- Reusable components
- Easier to test
- Clear separation of concerns

### Retry Logic

All scripts include automatic retry with exponential backoff:
- Default: 25 retry attempts
- Configurable via `--retry-limit`
- Separate retry counters for multi-stage processes

### Efficient Data Structures

Batch 1 uses sets for duplicate detection:
```python
answer_set = set()  # O(1) lookup
if response in answer_set:
    duplicate_count += 1
else:
    answer_set.add(response)
```

Legacy code used lists (O(n) lookup), which slowed down with large datasets.

## Model Mappings

The project now supports direct OpenRouter model IDs. You can use any model available on OpenRouter by passing its ID to the `--model` flag.

Examples:
- `anthropic/claude-3-opus`
- `openai/gpt-4o`
- `google/gemini-flash-1.5`

## Common Development Tasks

### Adding a New Model

No code changes required. Just use the new model ID in the CLI.

### Changing Default Parameters

Use CLI arguments:
```bash
uv run run_experiment.py batch1 --temperature 0.7 --max-tokens 500 --cycles 50
```

Or modify constants in the script:
```python
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 500
```

### Running Multiple Experiments

Use shell scripts or loops:
```bash
for model in anthropic/claude-3-sonnet openai/gpt-4o google/gemini-flash-1.5; do
    uv run run_experiment.py batch1 --model $model --cycles 100
done
```

## Migration from v1.0

The original implementation with model-specific scripts has been completely replaced. Key improvements:
- Eliminated 90% code duplication
- Removed hardcoded API keys (security risk)
- Replaced inefficient O(n) algorithms with O(1)
- Added proper CLI interface
- Unified API through OpenRouter

See git history for the original implementation if needed.

## Testing Platform

Scripts tested on:
- macOS (Darwin 25.0.0)
- Python 3.x
- OpenRouter API

Should work on any platform with Python 3.7+.

## Common Issues

**"OPENROUTER_API_KEY not found"**
- Create `.env` file from `.env.example`
- Add your API key

**"Unknown model"**
- Use `--help` to see available models
- Check model name spelling

**"Essay not found"**
- Verify essay file uses correct marker format
- Check essay number is within range
