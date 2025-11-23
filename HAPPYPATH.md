# Happy Path Testing: Phase 3 (Research & Content)

This document outlines the steps to verify the new Research and Citation features.

## Prerequisites
- `uv` installed
- Internet connection (for Semantic Scholar and CrossRef)
- (Optional) `OPENROUTER_API_KEY` set for full AI features (fallback mode works without it)

## 1. Setup
Create a test essay file:
```bash
echo "Artificial Intelligence in education is transforming how students learn. Personalized learning paths are becoming more common." > test_essay.txt
```

## 2. Research Assistant
Find relevant sources for your essay:
```bash
uv run python -m src.essay research test_essay.txt --min-sources 3
```
**Expected Output**:
- A list of 3 relevant academic papers with titles, authors, and years.
- If no API key is present, it uses the fallback search query.

## 3. Citation Generator
Generate a bibliography for the essay (assuming sources were added or just testing the generator):
```bash
uv run python -m src.essay cite test_essay.txt --generate-bibliography --style apa
```
**Expected Output**:
- Analysis of claims (if AI model available).
- A formatted bibliography in APA style (if sources were added/mocked).

## 4. Cleanup
```bash
rm test_essay.txt
```
