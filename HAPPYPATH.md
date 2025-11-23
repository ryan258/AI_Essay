# Happy Path Guide

This guide shows you the best way to use AI Essay for research, testing, and analysis. Follow these workflows to get the most out of the project.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Your First Experiment](#your-first-experiment)
3. [Common Workflows](#common-workflows)
4. [Research Use Cases](#research-use-cases)
5. [Best Practices](#best-practices)
6. [Advanced Techniques](#advanced-techniques)
7. [Troubleshooting Tips](#troubleshooting-tips)

---

## Initial Setup

### Step 1: Install and Configure (5 minutes)

```bash
# Clone and navigate to project
cd AI_Essay

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY from https://openrouter.ai/keys
```

### Step 2: Set Your Default Model (Optional but Recommended)

Edit `.env` to set a default model:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=anthropic/claude-3-sonnet
```

This saves you from typing `--model` every time!

### Step 3: Test Your Setup

```bash
# Quick test with 3 cycles
uv run run_experiment.py batch1 --cycles 3 --prompt "Hello, world!"
```

If this works, you're ready to go! 🎉

---

## Your First Experiment

### Understand Response Uniqueness (Batch 1)

**Goal**: See how creative/deterministic different models are.

```bash
# Test Claude's uniqueness
uv run run_experiment.py batch1 \
    --model anthropic/claude-3-sonnet \
    --cycles 20 \
    --prompt "Explain quantum computing in one sentence" \
    --output-dir results/uniqueness/claude

# Test GPT's uniqueness
uv run run_experiment.py batch1 \
    --model openai/gpt-4o \
    --cycles 20 \
    --prompt "Explain quantum computing in one sentence" \
    --output-dir results/uniqueness/gpt
```

**What to look for**:
- Uniqueness rate (higher = more creative)
- Response time patterns
- Word count consistency

**Typical Results**:
- Temperature 1.0: 70-100% unique responses
- Temperature 0.1: 10-30% unique responses (more consistent)

---

## Common Workflows

### Workflow 1: Compare Models on Same Task

**Use Case**: You want to know which model is best for your use case.

```bash
# Create a prompt file
cat > research_prompt.txt << 'EOF'
Write a 500-word essay about the impact of artificial intelligence on education.
Include specific examples and cite potential benefits and risks.
EOF

# Test multiple models
for model in anthropic/claude-3-sonnet openai/gpt-4o google/gemini-flash-1.5; do
    echo "Testing $model..."
    uv run run_experiment.py batch2 \
        --model $model \
        --prompt-file research_prompt.txt \
        --cycles 5 \
        --output-dir "results/comparison/$(basename $model)"
done

# Compare results
ls -lh results/comparison/*/essay.txt
```

**Analysis Questions**:
- Which model produces longer essays?
- Which has more varied vocabulary?
- Which follows instructions better?
- Which is fastest?

---

### Workflow 2: Test Temperature Effects

**Use Case**: Understand how temperature affects creativity vs consistency.

```bash
# Test different temperatures
for temp in 0.1 0.5 1.0 1.5; do
    echo "Testing temperature $temp..."
    uv run run_experiment.py batch1 \
        --model anthropic/claude-3-sonnet \
        --temperature $temp \
        --cycles 25 \
        --prompt "What is the meaning of life?" \
        --output-dir "results/temperature/temp_$temp"
done
```

**Expected Results**:
- **0.1**: Very consistent, low uniqueness (good for factual tasks)
- **0.5**: Balanced creativity and consistency
- **1.0**: Creative, varied responses (default)
- **1.5**: Highly creative, sometimes less coherent

---

### Workflow 3: Essay Generation Pipeline

**Use Case**: Generate essays and analyze their structure.

```bash
# Step 1: Generate 50 essays
uv run run_experiment.py batch2 \
    --model anthropic/claude-3-sonnet \
    --prompt-file examples/batch5/essay.txt \
    --cycles 50 \
    --output-dir results/essays/generated

# Step 2: Classify topics from generated essays
uv run run_experiment.py batch5 \
    --model openai/gpt-4o \
    --essay-file results/essays/generated/essay.txt \
    --cycles 50 \
    --output-dir results/essays/classified
```

**Analysis**:
```bash
# See topic distribution
sort results/essays/classified/topic.txt | uniq -c | sort -rn

# Find most common thesis patterns
grep -A 2 "Thesis number" results/essays/generated/thesis.txt | head -20
```

---

## Research Use Cases

### Use Case 1: Measuring Model Consistency

**Research Question**: How consistent is model X compared to model Y?

```bash
# Create test script
cat > test_consistency.sh << 'EOF'
#!/bin/bash
PROMPT="The capital of France is"

for model in anthropic/claude-3-sonnet openai/gpt-4o google/gemini-flash-1.5; do
    echo "Testing $model..."
    uv run run_experiment.py batch1 \
        --model $model \
        --cycles 100 \
        --prompt "$PROMPT" \
        --temperature 0.5 \
        --output-dir "results/consistency/$(basename $model)"
done
EOF

chmod +x test_consistency.sh
./test_consistency.sh
```

**Metrics to Analyze**:
- Duplicate percentage (lower = more consistent)
- Average response time
- Word count variance

---

### Use Case 2: Evaluating Instruction Following

**Research Question**: Which model best follows complex instructions?

```bash
# Create complex instruction
cat > complex_instruction.txt << 'EOF'
Write a 300-word essay about machine learning that:
1. Uses exactly 3 paragraphs
2. Includes the words "algorithm", "data", and "pattern" at least once each
3. Ends with a question for the reader
4. Uses a metaphor to explain a concept
EOF

# Test models
for model in anthropic/claude-3-opus anthropic/claude-3-sonnet openai/gpt-4o; do
    uv run run_experiment.py batch2 \
        --model $model \
        --prompt-file complex_instruction.txt \
        --cycles 10 \
        --output-dir "results/instruction_following/$model"
done
```

**Manual Analysis**:
- Check for 3 paragraphs
- Search for required words
- Verify question at end
- Count metaphors used

---

### Use Case 3: Cost-Effectiveness Analysis

**Research Question**: Which model gives best value for money?

```bash
# Test economical models
for model in openai/gpt-3.5-turbo google/gemini-flash-1.5 anthropic/claude-3-haiku; do
    echo "Testing $model..."
    time uv run run_experiment.py batch2 \
        --model $model \
        --prompt "Write a short essay about climate change" \
        --cycles 20 \
        --max-tokens 500 \
        --output-dir "results/cost_analysis/$(basename $model)"
done
```

**Compare**:
- OpenRouter dashboard for actual costs
- Quality of outputs (manual review)
- Speed of responses
- Cost per 1000 tokens

---

## Best Practices

### 1. Start Small, Scale Up

```bash
# ✅ GOOD: Test with 5 cycles first
uv run run_experiment.py batch1 --cycles 5 --model anthropic/claude-3-sonnet

# ❌ BAD: Don't start with 100 cycles before testing
# uv run run_experiment.py batch1 --cycles 100 --model expensive/model
```

### 2. Use Descriptive Output Directories

```bash
# ✅ GOOD: Clear, dated, descriptive names
uv run run_experiment.py batch1 \
    --output-dir "results/2024-11-21_uniqueness_claude_temp1.0"

# ❌ BAD: Generic names that you'll forget
# --output-dir "results/test1"
```

### 3. Save Your Prompts

```bash
# ✅ GOOD: Reusable, version-controlled prompts
cat > prompts/research_v2.txt << 'EOF'
Your detailed prompt here...
EOF

uv run run_experiment.py batch2 --prompt-file prompts/research_v2.txt

# ❌ BAD: Inline prompts that you can't reproduce
# --prompt "some long prompt that you'll forget"
```

### 4. Document Your Experiments

Create a research log:
```bash
# Create experiment log
cat >> research_log.md << 'EOF'
## 2024-11-21: Temperature Study

**Question**: How does temperature affect uniqueness?
**Models**: Claude Sonnet, GPT-4o
**Cycles**: 50 per temperature
**Temperatures**: 0.1, 0.5, 1.0, 1.5

**Results**:
- Claude 0.1: 15% unique
- Claude 1.0: 92% unique
- GPT 0.1: 23% unique
- GPT 1.0: 87% unique

**Conclusion**: Both models show similar patterns. Temperature 1.0 gives good variety.
EOF
```

### 5. Monitor Costs

```bash
# Before expensive experiments, test with cheaper models
uv run run_experiment.py batch1 \
    --model google/gemini-flash-1.5 \
    --cycles 10

# Once you verify it works, use premium models
uv run run_experiment.py batch1 \
    --model anthropic/claude-3-opus \
    --cycles 100
```

---

## Advanced Techniques

### Technique 1: Batch Processing with Different Prompts

```bash
# Create multiple prompt files
mkdir -p prompts/batch

cat > prompts/batch/prompt1.txt << 'EOF'
Write about technology...
EOF

cat > prompts/batch/prompt2.txt << 'EOF'
Write about education...
EOF

# Process all prompts
for prompt_file in prompts/batch/*.txt; do
    name=$(basename "$prompt_file" .txt)
    uv run run_experiment.py batch2 \
        --model anthropic/claude-3-sonnet \
        --prompt-file "$prompt_file" \
        --cycles 10 \
        --output-dir "results/batch/$name"
done
```

### Technique 2: Parallel Execution for Speed

```bash
# Run multiple experiments in parallel (be careful with API rate limits!)
uv run run_experiment.py batch1 --model anthropic/claude-3-sonnet --cycles 50 &
uv run run_experiment.py batch1 --model openai/gpt-4o --cycles 50 &
uv run run_experiment.py batch1 --model google/gemini-flash-1.5 --cycles 50 &
wait
```

### Technique 3: Configuration-Based Experiments

Edit `config.yaml` for your research:
```yaml
defaults:
  max_tokens: 2000  # Longer responses
  temperature: 0.7  # Slightly more consistent
  cycles: 50        # Standard experiment size
```

Then run without flags:
```bash
uv run run_experiment.py batch1  # Uses config defaults
```

### Technique 4: Custom Analysis Scripts

```python
# analyze_results.py
import re
from pathlib import Path

def analyze_uniqueness(results_dir):
    """Analyze uniqueness experiment results."""
    essay_file = Path(results_dir) / "essay.txt"

    with open(essay_file) as f:
        content = f.read()

    # Count essays
    essays = re.findall(r'\*\*\*\*\*\*\*\* Essay number: (\d+)', content)

    print(f"Total essays: {len(essays)}")
    print(f"Average length: {len(content) / len(essays):.0f} chars")

    return len(essays)

# Use it
analyze_uniqueness("results/claude_test")
```

---

## Troubleshooting Tips

### Issue: "OPENROUTER_API_KEY not found"

```bash
# Check your .env file
cat .env

# Should see:
# OPENROUTER_API_KEY=sk-or-v1-...

# If not, create it:
echo "OPENROUTER_API_KEY=your-key-here" > .env
```

### Issue: Rate Limiting

```bash
# Reduce cycles
uv run run_experiment.py batch1 --cycles 10  # instead of 100

# Add delays between experiments
uv run run_experiment.py batch1 --cycles 50
sleep 60  # Wait 1 minute
uv run run_experiment.py batch1 --cycles 50
```

### Issue: Running Out of Disk Space

```bash
# Check results size
du -sh results/

# Clean old results
rm -rf results/old_experiments/

# Or compress them
tar -czf results_backup.tar.gz results/
rm -rf results/
```

### Issue: Models Not Working

```bash
# Check available models at OpenRouter
# Visit: https://openrouter.ai/models

# Test with a known-good model
uv run run_experiment.py batch1 \
    --model openai/gpt-3.5-turbo \
    --cycles 3
```

---

## Example Research Projects

### Project 1: Model Comparison Study (1 hour)

```bash
# Setup
mkdir -p research/model_comparison
cd research/model_comparison

# Create prompt
cat > prompt.txt << 'EOF'
Write a persuasive essay about the importance of scientific literacy.
Include three main arguments with supporting evidence.
EOF

# Test all major models
for model in anthropic/claude-3-opus anthropic/claude-3-sonnet openai/gpt-4o google/gemini-flash-1.5; do
    uv run ../../run_experiment.py batch2 \
        --model $model \
        --prompt-file prompt.txt \
        --cycles 20 \
        --output-dir "$(basename $model)"
done

# Analyze
echo "Results:" > summary.txt
for dir in */; do
    echo "$dir: $(wc -l < $dir/essay.txt) lines" >> summary.txt
done
cat summary.txt
```

### Project 2: Temperature Optimization (30 minutes)

```bash
# Find optimal temperature for your use case
mkdir -p research/temperature_opt

PROMPT="Explain blockchain technology to a 10-year-old"

for temp in 0.0 0.3 0.7 1.0 1.3 1.7 2.0; do
    uv run run_experiment.py batch1 \
        --model anthropic/claude-3-sonnet \
        --temperature $temp \
        --cycles 30 \
        --prompt "$PROMPT" \
        --output-dir "research/temperature_opt/temp_$temp"
done

# Review uniqueness rates to find sweet spot
```

### Project 3: Cost vs Quality Analysis (2 hours)

```bash
# Compare cheap vs expensive models
mkdir -p research/cost_quality

# Cheap models
for model in openai/gpt-3.5-turbo google/gemini-flash-1.5; do
    uv run run_experiment.py batch2 \
        --model $model \
        --prompt "Write a detailed explanation of machine learning" \
        --cycles 50 \
        --output-dir "research/cost_quality/cheap_$(basename $model)"
done

# Expensive models
for model in anthropic/claude-3-opus openai/gpt-4o; do
    uv run run_experiment.py batch2 \
        --model $model \
        --prompt "Write a detailed explanation of machine learning" \
        --cycles 50 \
        --output-dir "research/cost_quality/expensive_$(basename $model)"
done

# Manual quality review + OpenRouter cost dashboard = data!
```

---

## Quick Reference

### Most Common Commands

```bash
# Quick test (batch1)
uv run run_experiment.py batch1 --cycles 5

# Essay generation (batch2)
uv run run_experiment.py batch2 --prompt-file my_prompt.txt --cycles 20

# Topic classification (batch5)
uv run run_experiment.py batch5 --essay-file essays.txt --cycles 50

# Model comparison
for model in anthropic/claude-3-sonnet openai/gpt-4o; do
    uv run run_experiment.py batch1 --model $model --cycles 10
done

# Temperature test
for temp in 0.1 0.5 1.0; do
    uv run run_experiment.py batch1 --temperature $temp --cycles 20
done
```

### Recommended Models by Use Case

| Use Case | Recommended Model | Reason |
|----------|------------------|--------|
| **Testing/Development** | `google/gemini-flash-1.5` | Fast and cheap |
| **Quality Research** | `anthropic/claude-3-opus` | Best quality |
| **Balanced** | `anthropic/claude-3-sonnet` | Good quality, reasonable cost |
| **High Volume** | `openai/gpt-3.5-turbo` | Fastest, cheapest |
| **Technical Tasks** | `openai/gpt-4o` | Strong reasoning |

### Recommended Cycle Counts

| Purpose | Cycles | Reason |
|---------|--------|--------|
| **Testing setup** | 3-5 | Verify it works |
| **Quick check** | 10-20 | Get a feel for behavior |
| **Research** | 50-100 | Statistical significance |
| **Production** | 100+ | Comprehensive data |

---

## Next Steps

1. **Start Simple**: Run the "Your First Experiment" section
2. **Pick a Use Case**: Choose from "Research Use Cases"
3. **Follow Best Practices**: Reference "Best Practices" section
4. **Scale Up**: Move to "Advanced Techniques"
5. **Contribute**: Share your findings, improve the tool

## Getting Help

- **Documentation**: See `README.md` for full reference
- **Development**: See `CLAUDE.md` for architecture
- **Issues**: Check `ROADMAP.md` for known issues
- **Quick Start**: See `QUICKSTART.md` for basics

---

**Happy Researching! 🎉**
