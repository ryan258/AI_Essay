# AI Essay

AI Essay is a research project exploring AI model responses, focusing on essay generation, classification, and response uniqueness testing across multiple models (Claude, GPT, Gemini, and Grok).

**Author**: Stephen Witty (switty@level500.com)
**Collaborator**: Hannah Witty

## Features

- **Unified API**: Access all models through OpenRouter with a single API key
- **Modular Architecture**: Clean, maintainable codebase with proper separation of concerns
- **Response Uniqueness Testing**: Measure how often models produce duplicate responses
- **Essay Generation**: Generate essays and automatically extract thesis statements
- **Topic Classification**: Classify essay topics from pre-generated content
- **Multi-Model Support**: Test Claude, GPT, Gemini, and Grok with the same code
- **CLI Interface**: Easy command-line usage with YAML configuration
- **Metrics Tracking**: Comprehensive statistics on responses, timing, and word counts

## Quick Start

### 1. Install Dependencies

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_key_here
```

Get an API key from https://openrouter.ai/keys

### 3. Run an Experiment

```bash
# Test response uniqueness
uv run run_experiment.py batch1 --model anthropic/claude-3-sonnet --cycles 10

# Generate essays and extract theses
uv run run_experiment.py batch2 --model openai/gpt-4o --prompt "Write an essay about creativity" --cycles 5

# Classify essay topics
uv run run_experiment.py batch5 --model google/gemini-flash-1.5 --essay-file examples/batch5/essay.txt --cycles 10
```

## Project Structure

```
AI_Essay/
├── run_experiment.py       # Main CLI entry point ⭐
├── config.yaml             # Experiment configuration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── CLAUDE.md              # Developer documentation
├── ROADMAP.md             # Refactoring plan
├── src/
│   ├── __init__.py
│   ├── experiment.py      # Experiment runners
│   ├── metrics.py         # Statistics collection
│   ├── utils.py           # Shared utilities
│   └── models/
│       ├── __init__.py
│       ├── base.py        # Abstract base class
│       └── openrouter.py  # OpenRouter implementation
├── examples/
│   └── batch5/            # Example files (essays, topics)
├── results/               # Output directory (created automatically)
│   ├── batch1/
│   ├── batch2/
│   └── batch5/
└── tests/                 # Unit tests
```

## Experiments

### Batch 1: Response Uniqueness Testing

Tests how often AI models generate duplicate responses when given the same prompt multiple times.

**Usage:**
```bash
python run_experiment.py batch1 --model claude-sonnet-4 --cycles 100
```

**With custom prompt:**
```bash
python run_experiment.py batch1 \
    --model gpt-4o \
    --prompt "How many Rs are in the word strawberry?" \
    --cycles 50 \
    --temperature 1.0
```

**Output:**
- Duplicate rate statistics
- Response time metrics
- Word count analysis
- Sample unique responses (printed to console)

### Batch 2: Essay Generation + Thesis Extraction

Two-stage process that generates essays and then extracts thesis statements from them.

**Usage:**
```bash
python run_experiment.py batch2 --model claude-sonnet-4 --prompt-file prompt.txt --cycles 100
```

**With inline prompt:**
```bash
python run_experiment.py batch2 \
    --model gemini-2.5-flash \
    --prompt "Write a literacy narrative about learning to read" \
    --cycles 10 \
    --output-dir results/gemini/
```

**Output Files:**
- `results/batch2/essay.txt`: Generated essays
- `results/batch2/thesis.txt`: Extracted thesis statements

### Batch 5: Topic Classification

Classifies topics from pre-generated essays.

**Usage:**
```bash
python run_experiment.py batch5 --model claude-sonnet-4 --essay-file examples/batch5/essay.txt --cycles 100
```

**With custom output:**
```bash
python run_experiment.py batch5 \
    --model gpt-4o \
    --essay-file my_essays.txt \
    --output-dir results/topics/ \
    --cycles 50
```

**Input Format:**
Essays must be in a text file with markers:
```
******** Essay number: 1 ************
[Essay content here]

******** Essay number: 2 ************
[Essay content here]
```

**Output:**
- `results/batch5/topic.txt`: Classified topics

## Configuration

The `config.yaml` file contains default settings for all experiments:

```yaml
defaults:
  max_tokens: 1000
  temperature: 1.0
  retry_limit: 25
  cycles: 100

experiments:
  batch1:
    default_prompt: "How many Rs are in the word strawberry?"
    output_dir: "results/batch1"
  # ... etc
```

You can override these settings via command-line arguments.

## Supported Models

| Model Name | Provider | Description |
|-----------|----------|-------------|
| `anthropic/claude-3-opus` | Anthropic | Most capable Claude model |
| `anthropic/claude-3-sonnet` | Anthropic | Balanced performance/cost |
| `openai/gpt-4o` | OpenAI | GPT-4 optimized |
| `openai/gpt-3.5-turbo` | OpenAI | Fast and economical |
| `google/gemini-flash-1.5` | Google | Fast Gemini model |
| `x-ai/grok-beta` | xAI | Grok model |

**Note**: You can use ANY model available on OpenRouter. Just pass the full model ID (e.g., `meta-llama/llama-3-70b-instruct`) to the `--model` flag.

## Command-Line Options

### Common Options (All Experiments)

- `--model`: AI model to use (required)
- `--cycles`: Number of iterations to run
- `--temperature`: Sampling temperature 0.0-2.0
- `--max-tokens`: Maximum tokens in response
- `--retry-limit`: Max API retry attempts
- `--output-dir`: Directory for output files
- `--config`: Path to config file (default: config.yaml)

### Batch-Specific Options

**Batch 1:**
- `--prompt`: Custom prompt text
- `--prompt-file`: File containing prompt

**Batch 2:**
- `--prompt`: Essay generation prompt (inline)
- `--prompt-file`: File containing essay prompt
- `--thesis-prompt`: Custom thesis extraction prompt

**Batch 5:**
- `--essay-file`: File containing pre-generated essays (required)
- `--topic-prompt`: Custom topic classification prompt

## Examples

### Compare Models on Same Task

```bash
for model in claude-sonnet-4 gpt-4o gemini-2.5-flash; do
    python run_experiment.py batch1 \
        --model $model \
        --cycles 100 \
        --prompt "What is the meaning of life?" \
        --output-dir "results/batch1/$model"
done
```

### Generate Essays with Different Temperatures

```bash
for temp in 0.1 0.5 1.0 1.5; do
    python run_experiment.py batch2 \
        --model claude-sonnet-4 \
        --prompt-file literacy_prompt.txt \
        --temperature $temp \
        --output-dir "results/batch2/temp_$temp"
done
```

## Architecture Highlights

### Object-Oriented Design

- **Abstract Base Class**: `AIModel` defines interface for all models
- **Model Implementations**: `OpenRouterModel` provides unified access
- **Experiment Classes**: `UniquenessExperiment`, `EssayExperiment`, `TopicClassificationExperiment`
- **Metrics Collection**: `MetricsCollector` tracks statistics with efficient data structures

### Key Improvements Over Legacy Code

1. **90% Code Reduction**: Single unified codebase instead of 20+ duplicate scripts
2. **Security**: Environment variables, no hardcoded API keys
3. **Efficiency**:
   - API client reused (not recreated per call)
   - O(1) duplicate detection using sets
   - Proper retry logic without bugs
4. **Maintainability**:
   - Proper separation of concerns
   - Type hints and docstrings
   - Configuration via YAML
   - Easy to add new models or experiments

## Development

### Running Tests

```bash
pytest tests/
```

### Adding a New Model

No code changes are required to add a new model! Simply find the model ID on [OpenRouter](https://openrouter.ai/models) and pass it to the `--model` flag.

Example:
```bash
uv run run_experiment.py batch1 --model meta-llama/llama-3-70b-instruct
```

### Creating a New Experiment Type

1. Create experiment class in `src/experiment.py` inheriting from `ExperimentRunner`
2. Implement `run()` method
3. Add configuration to `config.yaml`
4. Add CLI handler in `run_experiment.py`

See `CLAUDE.md` for detailed developer documentation.

## Why OpenRouter?

The refactored version uses OpenRouter instead of individual provider APIs:

1. **Single API Key**: One key for all models instead of managing 4+ provider keys
2. **Unified Interface**: Same code works with Claude, GPT, Gemini, and Grok
3. **Simplified Setup**: Install one package (openai) instead of 4+ SDKs
4. **Easy Model Switching**: Change `--model` flag instead of editing code
5. **Cost Tracking**: Centralized billing and usage tracking

## Version History

**v2.0**: Complete refactor with modular architecture, OpenRouter integration, and YAML configuration.

**v1.0**: Original implementation (removed - see git history if needed).

## Requirements

- Python 3.7+
- Internet connection for API calls
- OpenRouter API key

## Cost Considerations

OpenRouter charges per token based on the model used. Start with small `--cycles` values (5-10) when testing.

## Troubleshooting

**"OPENROUTER_API_KEY not found"**
```bash
# Make sure .env file exists and contains your key
cat .env
```

**"Unknown model"**
```bash
# List available models
python run_experiment.py batch1 --help
```

**"Essay not found" (Batch 5)**
```bash
# Verify essay file format has correct markers
grep "Essay number:" your_essay_file.txt
```

**Module not found**
```bash
# Install dependencies
uv pip install -r requirements.txt
```

## License

Contact Stephen Witty (switty@level500.com) for licensing information.

## Contributing

This is a research project. For questions or collaboration opportunities, contact the author.

## Citation

If you use this code in your research, please cite:
```
AI Essay Project
Stephen Witty & Hannah Witty
2024-2025
```
