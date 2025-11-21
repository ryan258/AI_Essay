# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
uv pip install -r requirements.txt
```

This installs:
- `openai` - For OpenRouter API (unified access to all models)
- `python-dotenv` - For environment variable management
- `pyyaml` - For configuration file parsing

### 2. Configure API Key
```bash
# Copy template
cp .env.example .env

# Edit .env and add your key
# OPENROUTER_API_KEY=your_key_here
```

Get your API key from https://openrouter.ai/keys

### 3. Run Your First Experiment
```bash
# Test response uniqueness with 5 cycles (fast)
uv run run_experiment.py batch1 \
    --model anthropic/claude-3-sonnet \
    --cycles 5 \
    --prompt "What color is the sky?"
```

Expected output:
```
================================================================================
RESPONSE UNIQUENESS EXPERIMENT
================================================================================
Model: OpenRouterModel(model_name='anthropic/claude-3-sonnet', max_tokens=1000, temperature=1.0)
Cycles: 5

Prompt:
What color is the sky?
--------------------------------------------------------------------------------

Cycle: 1/5 | Duplicates: 0 | Time: 1.23s
The sky appears blue...

...

================================================================================
FINAL REPORT
================================================================================
...
Uniqueness rate: 100.0%
```

## Example Workflows

### Test All Models on Same Prompt
```bash
for model in anthropic/claude-3-sonnet openai/gpt-4o google/gemini-flash-1.5; do
    uv run run_experiment.py batch1 \
        --model $model \
        --cycles 10 \
        --prompt "How many Rs are in strawberry?" \
        --output-dir "results/batch1/$(basename $model)"
done
```

### Generate Essays
```bash
# Create a prompt file
cat > my_prompt.txt << 'EOF'
Write a literacy narrative about a time you learned something new.
Reflect on how this experience changed your understanding.
EOF

# Generate 10 essays
uv run run_experiment.py batch2 \
    --model anthropic/claude-3-sonnet \
    --prompt-file my_prompt.txt \
    --cycles 10 \
    --output-dir results/my_essays

# Results will be in:
# - results/my_essays/essay.txt
# - results/my_essays/thesis.txt
```

### Classify Essay Topics
```bash
uv run run_experiment.py batch5 \
    --model openai/gpt-4o \
    --essay-file examples/batch5/essay.txt \
    --cycles 20 \
    --output-dir results/topics

# Results in: results/topics/topic.txt
```

### Adjust Temperature for Variation
```bash
# Low temperature (more consistent)
uv run run_experiment.py batch1 \
    --model anthropic/claude-3-sonnet \
    --temperature 0.1 \
    --cycles 20

# High temperature (more creative/varied)
uv run run_experiment.py batch1 \
    --model anthropic/claude-3-sonnet \
    --temperature 1.5 \
    --cycles 20
```

## Configuration

All experiments can be configured via:

1. **config.yaml** - Default settings
2. **Command-line arguments** - Override defaults

### View All Options
```bash
uv run run_experiment.py --help
uv run run_experiment.py batch1 --help
uv run run_experiment.py batch2 --help
uv run run_experiment.py batch5 --help
```

### Common Options
- `--model` - AI model to use (required)
- `--cycles` - Number of iterations
- `--temperature` - Sampling temperature (0.0-2.0)
- `--max-tokens` - Maximum tokens in response
- `--retry-limit` - Max API retry attempts
- `--output-dir` - Directory for results

## Project Files

### You Should Edit
- `.env` - Your API key
- `config.yaml` - Default experiment settings
- Custom prompt files

### You Should Run
- `run_experiment.py` - Main CLI

### You Should Read
- `README.md` - Full documentation
- `CLAUDE.md` - Developer guide
- `config.yaml` - Configuration reference

### You Should NOT Edit (Unless Developing)
- `src/` - Source code
- `examples/` - Sample data
- `requirements.txt` - Dependencies

## Next Steps

1. **Read the full README.md** for detailed documentation
2. **Explore config.yaml** to understand default settings
3. **Check examples/batch5/** for sample input/output
4. **See CLAUDE.md** if you want to extend the code

## Troubleshooting

**"No module named 'yaml'"**
```bash
uv pip install -r requirements.txt
```

**"OPENROUTER_API_KEY not found"**
```bash
# Make sure .env exists and has your key
cat .env
```

**"Unknown model"**
```bash
# Available models: Any OpenRouter model ID
# Examples: anthropic/claude-3-opus, openai/gpt-4o, google/gemini-flash-1.5
```

## Cost Tips

- Start with `--cycles 5` to test before running 100 cycles
- Use `gpt-3.5-turbo` or `gemini-2.5-flash` for economical testing
- Monitor your OpenRouter usage at https://openrouter.ai/activity
