# AI Essay: Your Thinking Partner for Truth-Seeking

**AI Essay** is a personal CLI tool that uses multiple AI models to help you create exceptional written content. It's not about writing faster—it's about thinking deeper, exposing weak reasoning, and mining for truth through rigorous intellectual exploration.

**Author**: Stephen Witty (switty@level500.com)
**Collaborator**: Hannah Witty

---

## Philosophy

Exceptional writing emerges from rigorous thinking. This tool uses AI models as tireless critics and thinking partners—each challenging your ideas from different angles to push your reasoning to levels of depth and clarity difficult to achieve alone.

**Core Values:**
- **Truth over productivity**: Better thinking matters more than faster writing
- **Rigor over ease**: Expose flaws in reasoning, even when uncomfortable
- **Multi-perspective**: Different models challenge assumptions in different ways
- **Evidence-based**: Claims require support; speculation requires acknowledgment
- **Iterative refinement**: Good ideas become exceptional through repeated scrutiny

---

## Quick Start

### 1. Install Dependencies

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_key_here
# Optional: default model for all commands (can be overridden with --model)
# OPENROUTER_MODEL=anthropic/claude-3-haiku

# Optional: per-role defaults (override OPENROUTER_MODEL for specific tasks)
# MODEL_ANALYZE=anthropic/claude-3-sonnet       # analyze
# MODEL_ARGUMENT=anthropic/claude-3-opus        # analyze-argument
# MODEL_OPTIMIZE=openai/gpt-4o                  # optimize
# MODEL_RESEARCH=google/gemini-flash-1.5        # research
# MODEL_CITE=anthropic/claude-3-haiku           # cite
# MODEL_FACTCHECK=anthropic/claude-3-haiku      # check_plagiarism / fact checks
# MODEL_SUMMARIZE=anthropic/claude-3-haiku      # summarize
# MODEL_OUTLINE=google/gemini-flash-1.5         # outline
```

Get an API key from https://openrouter.ai/keys

### 3. (Optional) Advanced Configuration

For additional customization, create a `config.yaml` file:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` to customize default settings:

```yaml
defaults:
  max_tokens: 1000     # Maximum tokens for API responses
  temperature: 1.0     # Creativity level (0.0-2.0)
  retry_limit: 3       # Retry attempts for failed API calls
```

**Configuration Precedence** (highest to lowest):
1. **CLI arguments** - Flags like `--model`, `--temperature` override everything
2. **Environment variables** - Settings in `.env` file
3. **Config file** - Settings in `config.yaml`
4. **Default values** - Built-in fallbacks

### 4. Install System Dependencies (for PDF export)

```bash
# macOS
brew install cairo pango gdk-pixbuf libffi

# Ubuntu/Debian
sudo apt-get install libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0
```

---

## The Happy Path: Complete Workflow

### Beginner Path: Interactive Wizard

The easiest way to create an essay is with the interactive wizard:

```bash
uv run python -m src.essay wizard
```

The wizard guides you step-by-step through:
1. **Topic selection**: What are you writing about?
2. **Template choice**: Argumentative or research paper?
3. **Word count target**: How long should it be?
4. **Research**: Find sources automatically?
5. **Outline generation**: Create structure
6. **Draft generation**: Generate full draft (optional)

Output is saved to timestamped directories like `wizard_output/20241124_143022_your_topic/`

---

### Advanced Path: Command-by-Command Workflow

For experienced users who want fine-grained control:

#### 1. Generate Multiple Drafts (Multi-Perspective)

```bash
uv run python -m src.essay draft \
    "The Impact of AI on Education" \
    --models "anthropic/claude-3-haiku,openai/gpt-3.5-turbo,google/gemini-flash-1.5"
```

**Why multiple models?** Each AI has different strengths and biases. Comparing drafts reveals blind spots and generates diverse perspectives you can synthesize.

**Output**: Creates timestamped directory with 3 separate drafts for comparison.

---

#### 2. Create an Outline First (Structure Thinking)

```bash
uv run python -m src.essay outline \
    --topic "Climate Change Policy" \
    --template argumentative \
    --word-count 1500
```

**Why start with an outline?** Forces you to think through structure and logic before writing. Reveals gaps in your argument early.

**Output**: `outline.md` with thesis, main points, and suggested structure.

---

#### 3. Analyze Structure (Find Gaps)

```bash
uv run python -m src.essay analyze my_draft.txt
```

**What it checks:**
- Thesis statement present and clear?
- Topic sentences in each paragraph?
- Logical flow and transitions?
- Introduction and conclusion strength?

**Output**: Structure report with scores and specific recommendations.

---

#### 4. Analyze Arguments (Expose Fallacies)

```bash
uv run python -m src.essay analyze-argument my_draft.txt
```

**What it detects:**
- Logical fallacies (ad hominem, straw man, circular reasoning, etc.)
- Weak claims without evidence
- Missing counterarguments
- Argument strength score (1-10)

**Output**: Detailed analysis of reasoning quality with improvement suggestions.

---

#### 5. Optimize Grammar & Clarity (Remove Noise)

```bash
uv run python -m src.essay optimize my_draft.txt --apply-fixes
```

**What it improves:**
- Grammar and spelling
- Wordiness and unclear sentences
- Passive voice → active voice
- Clichés and weak verbs
- Readability (Flesch-Kincaid grade level)

**Output**: Cleaned version with metrics showing improvements.

---

#### 6. Add Research & Citations (Ground in Evidence)

```bash
uv run python -m src.essay research my_draft.txt --min-sources 5
```

**What it does:**
- Finds relevant academic papers
- Identifies claims needing citations
- Suggests quotes to support arguments
- Performs gap analysis (what's missing?)

**Output**: Sources file with relevant papers and quotes.

Then add citations:

```bash
uv run python -m src.essay cite my_draft.txt \
    --style APA \
    --generate-bibliography \
    --lenient-fallback  # optional: use when you want every claim to get a citation even if relevance is low
```

**Output**: Essay with inline citations and full bibliography.

---

#### 7. Iterative Improvement (Push to Excellence)

```bash
uv run python -m src.essay improve my_draft.txt \
    --cycles 5 \
    --target-score 85
```

**What it does:**
- Runs multiple improvement cycles
- Tracks clarity, grammar, and argument scores
- Stops when target reached or no progress for 2 cycles
- Shows before/after for each iteration

**Output**: Improved essay with progress metrics.

---

#### 8. Export to Professional Format

```bash
# PDF (academic formatting)
uv run python -m src.essay export my_essay.md --format pdf

# Microsoft Word
uv run python -m src.essay export my_essay.md --format docx

# HTML (styled)
uv run python -m src.essay export my_essay.md --format html
```

**Output**: Professionally formatted document ready for submission.

---

### The Complete Workflow (All Steps)

```bash
# 1. Start with outline
uv run python -m src.essay outline --topic "AI Ethics" --template argumentative

# 2. Generate multiple drafts
uv run python -m src.essay draft "AI Ethics" --models "anthropic/claude-3-haiku,openai/gpt-3.5-turbo"

# 3. Analyze structure
uv run python -m src.essay analyze drafts/20241124_*/claude.txt

# 4. Check arguments for fallacies
uv run python -m src.essay analyze-argument drafts/20241124_*/claude.txt

# 5. Add research and citations
uv run python -m src.essay research drafts/20241124_*/claude.txt --min-sources 5
uv run python -m src.essay cite drafts/20241124_*/claude.txt --style APA

# 6. Optimize clarity
uv run python -m src.essay optimize drafts/20241124_*/claude.txt --apply-fixes

# 7. Iteratively improve
uv run python -m src.essay improve drafts/20241124_*/claude.txt --cycles 5

# 8. Export final version
uv run python -m src.essay export final_essay.md --format pdf
```

**Result**: An essay that has been analyzed from multiple angles, grounded in evidence, scrubbed for fallacies, and refined to exceptional quality.

---

## Available Commands

### Essay Creation

| Command | Purpose | Example |
|---------|---------|---------|
| `wizard` | Interactive guided workflow | `uv run python -m src.essay wizard` |
| `draft` | Generate essays with multiple models | `uv run python -m src.essay draft "Topic" --models "claude,gpt"` |
| `outline` | Create structured outline | `uv run python -m src.essay outline --topic "..." --template argumentative` |
| `new` | Create from template | `uv run python -m src.essay new "Topic" --template argumentative` |

### Analysis & Improvement

| Command | Purpose | Example |
|---------|---------|---------|
| `analyze` | Check structure and flow | `uv run python -m src.essay analyze essay.txt` |
| `analyze-argument` | Detect fallacies, rate strength | `uv run python -m src.essay analyze-argument essay.txt` |
| `optimize` | Improve grammar and clarity | `uv run python -m src.essay optimize essay.txt --apply-fixes` |
| `improve` | Iterative multi-cycle improvement | `uv run python -m src.essay improve essay.txt --cycles 5` |

### Research & Citations

| Command | Purpose | Example |
|---------|---------|---------|
| `research` | Find academic sources | `uv run python -m src.essay research essay.txt --min-sources 5` |
| `cite` | Add citations and bibliography | `uv run python -m src.essay cite essay.txt --style APA` |

### Templates & Export

| Command | Purpose | Example |
|---------|---------|---------|
| `templates list` | Show available templates | `uv run python -m src.essay templates list` |
| `export` | Convert to PDF/DOCX/HTML | `uv run python -m src.essay export essay.md --format pdf` |

---

## Features by Category

### 🎯 Core Creation
- ✅ **Multi-model drafting**: Generate essays from 2-5 AI models simultaneously
- ✅ **Smart outlines**: 4 template types (argumentative, analytical, comparative, 5-paragraph)
- ✅ **Template library**: Pre-built essay structures with user customization
- ✅ **Interactive wizard**: Guided step-by-step essay creation

### 🔍 Analysis & Improvement
- ✅ **Structure analyzer**: Detect thesis, topic sentences, flow issues
- ✅ **Argument analyzer**: Find logical fallacies, rate claim strength
- ✅ **Grammar optimizer**: Fix errors, improve clarity, eliminate wordiness
- ✅ **Readability metrics**: Flesch-Kincaid grade level, passive voice detection
- ✅ **Iterative improvement**: Multi-cycle refinement with progress tracking

### 📚 Research & Truth
- ✅ **Source finding**: Semantic Scholar integration for academic papers
- ✅ **Citation management**: APA, MLA, IEEE, Chicago styles
- ✅ **Gap analysis**: Identify missing evidence and unsupported claims
- ✅ **Auto-bibliography**: Generate formatted reference lists
- ✅ **Claim detection**: Find statements needing citations

### 📄 Export & Formatting
- ✅ **PDF export**: Academic formatting (Times New Roman, 12pt, double-spaced)
- ✅ **DOCX export**: Microsoft Word compatible
- ✅ **HTML export**: Styled web pages
- ✅ **Markdown**: Native format for all operations

---

## Project Structure

```
AI_Essay/
├── src/
│   ├── essay.py           # Main CLI entry point ⭐
│   ├── analyzer.py        # Structure analysis
│   ├── argument.py        # Fallacy detection & argument analysis
│   ├── citations.py       # Citation management
│   ├── export.py          # PDF/DOCX/HTML export
│   ├── improver.py        # Iterative improvement engine
│   ├── optimizer.py       # Grammar & clarity optimization
│   ├── outline.py         # Outline generation
│   ├── research.py        # Source finding & gap analysis
│   ├── templates.py       # Template library manager
│   ├── wizard.py          # Interactive wizard
│   └── templates/         # Built-in templates
├── tests/                 # 104 passing tests
├── examples/              # Example essays and topics
├── ROADMAP.md            # Development roadmap
├── CLAUDE.md             # Developer documentation
└── README.md             # This file
```

---

## Customization

### User Templates

Create custom templates in `~/.essay-templates/`:

```yaml
# ~/.essay-templates/my_template.yaml
name: "My Custom Template"
description: "Template for my writing style"
structure:
  - Introduction
  - Main Points
  - Conclusion
word_count_distribution:
  introduction: 15%
  body: 70%
  conclusion: 15%
```

Use it:
```bash
uv run python -m src.essay new "Topic" --template my_template
```

---

## Testing

All features are thoroughly tested:

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -xvs

# Run specific test file
uv run pytest tests/test_argument.py
```

**Current status**: ✅ 104 tests passing

---

## Why This Tool?

### Not Another Essay Generator

Most AI writing tools focus on speed: generate an essay in 30 seconds and move on. **AI Essay** takes the opposite approach: use AI to think *deeper*, not faster.

### Multi-Model Truth-Seeking

Running the same prompt through Claude, GPT, and Gemini reveals:
- Different interpretations of the question
- Diverse evidence and examples
- Alternative argument structures
- Blind spots in single-model responses

The synthesis of these perspectives yields richer, more nuanced content.

### Rigorous Self-Critique

The argument analyzer doesn't just check grammar—it exposes:
- Logical fallacies you didn't notice
- Claims made confidently without evidence
- Weak reasoning disguised by confident language
- Counterarguments you're avoiding

It forces intellectual honesty.

### Evidence-Based Writing

The research integration ensures:
- Key claims backed by peer-reviewed sources
- Citations in proper academic format
- Gap analysis reveals missing evidence
- Fact-checking catches confident falsehoods

---

## Cost & API Usage

AI Essay uses OpenRouter to access multiple AI models with a single API key.

**Typical costs** (approximate):
- Draft generation (3 models, 1000 words each): ~$0.15-0.50
- Analysis operations: ~$0.01-0.05 each
- Iterative improvement (5 cycles): ~$0.20-0.75
- Research & citations: ~$0.05-0.15

**Monthly estimate** for regular use: $10-50 depending on frequency

**Cost control**:
- Use cheaper models for drafts (Haiku, GPT-3.5-Turbo)
- Set API limits in OpenRouter dashboard
- Cache results locally to avoid re-processing

---

## Supported AI Models

AI Essay works with **any model available on OpenRouter**. Common choices:

| Model | Provider | Best For | Cost |
|-------|----------|----------|------|
| `anthropic/claude-3-haiku` | Anthropic | Fast drafts | $ |
| `anthropic/claude-3-sonnet` | Anthropic | Balanced quality/cost | $$ |
| `anthropic/claude-3-opus` | Anthropic | Deep analysis | $$$ |
| `openai/gpt-3.5-turbo` | OpenAI | Quick generation | $ |
| `openai/gpt-4o` | OpenAI | High quality | $$$ |
| `google/gemini-flash-1.5` | Google | Fast & cheap | $ |
| `google/gemini-pro-1.5` | Google | Research tasks | $$ |

See full list: https://openrouter.ai/models

---

## Troubleshooting

### "OPENROUTER_API_KEY not found"
```bash
# Check .env file exists
cat .env

# Should contain:
OPENROUTER_API_KEY=your_key_here
```

### PDF Export Fails
```bash
# Install system dependencies
# macOS:
brew install cairo pango gdk-pixbuf

# Ubuntu:
sudo apt-get install libcairo2 libpango-1.0-0
```

### Module Not Found
```bash
# Reinstall dependencies
uv pip install -r requirements.txt
```

### API Rate Limits
```bash
# Use slower, cheaper models
uv run python -m src.essay draft "Topic" --models "anthropic/claude-3-haiku"

# Or add delays between requests (edit src/essay.py)
```

---

## Legacy Features: Research Experiments (v2.0)

The original AI Essay project focused on testing AI model behaviors. These experiments are still available but no longer the primary focus:

```bash
# Test response uniqueness
uv run run_experiment.py batch1 --model anthropic/claude-3-sonnet --cycles 100

# Generate essays and extract theses
uv run run_experiment.py batch2 --model openai/gpt-4o --prompt "..." --cycles 10

# Classify essay topics
uv run run_experiment.py batch5 --model google/gemini-flash-1.5 --essay-file essays.txt
```

See `CLAUDE.md` for documentation on these legacy features.

---

## Development

### Architecture

- **CLI Framework**: Fire for command routing
- **AI Integration**: OpenRouter for unified API access
- **Research APIs**: Semantic Scholar, CrossRef
- **Export**: markdown2, weasyprint, python-docx
- **Testing**: pytest (104 tests)

### Contributing

This is a personal project. For questions or collaboration: switty@level500.com

---

## Version History

**v3.3 (November 2024)** - Current
- ✅ Template library with user customization
- ✅ Interactive wizard for guided workflow
- ✅ Export to PDF, DOCX, HTML

**v3.2 (November 2024)**
- ✅ Research integration with gap analysis
- ✅ Citation management (APA, MLA, IEEE, Chicago)
- ✅ Automatic bibliography generation

**v3.1 (November 2024)**
- ✅ Outline generator with 4 templates
- ✅ Grammar & clarity optimizer
- ✅ Argument analyzer with fallacy detection

**v3.0 (November 2024)**
- ✅ Multi-model essay drafting
- ✅ Structure analyzer
- ✅ Iterative improvement engine

**v2.0 (November 2024)**
- Original research tool with OpenRouter integration

---

## License

Contact Stephen Witty (switty@level500.com) for licensing information.

---

## Citation

If you use this tool in your research:
```
AI Essay: A Multi-Model Thinking Partner for Truth-Seeking
Stephen Witty & Hannah Witty
2024-2025
```

---

**The goal isn't to write essays faster. It's to think deeper, expose weak reasoning, and mine for truth. 🔍**
