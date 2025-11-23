# Known Issues & Limitations

This document tracks known issues, limitations, and external dependencies that affect AI Essay functionality.

**Last Updated**: November 23, 2024

---

## Phase 3: Research & Citations

### Semantic Scholar API Performance

**Issue**: Research assistant (`uv run python -m src.essay research`) may hang or timeout when searching for papers.

**Cause**: External API dependency on Semantic Scholar. API response times vary significantly based on:
- Network connectivity
- API rate limiting
- Query complexity
- Server load

**Current Mitigation**:
- Added 30-second timeout to SemanticScholar client
- Better error handling and logging
- Graceful fallback with error messages

**Workaround**:
- Use mocked tests for development (`pytest tests/test_research.py`)
- Retry failed searches after a few minutes
- Consider alternative APIs (OpenAlex, CrossRef) in future versions

**Status**: Documented limitation - not a bug in our code

**Future Fix**:
- Implement caching layer for common queries
- Add multiple fallback APIs (Phase 3.3)
- Implement async/parallel searches
- Add offline/demo mode with sample data

---

### CSL Style File Dependencies

**Issue**: Bibliography generation requires CSL (Citation Style Language) files in `styles/` directory.

**Current State**:
- ✅ APA, MLA, Chicago, IEEE styles included
- ⚠️ Additional styles require manual download

**Workaround**: Download additional styles from https://github.com/citation-style-language/styles

**Future Fix**: Auto-download missing styles on first use (Phase 3.3)

---

## Testing Infrastructure

### Module Import Path

**Issue**: Tests couldn't import `src` module initially.

**Fix**: Added `tests/conftest.py` to add project root to Python path.

**Status**: ✅ RESOLVED (November 23, 2024)

---

## Missing Features (Roadmap Items)

### Phase 1: Core Essay Creation - NOT STARTED

The following features from the roadmap are not yet implemented:
- Multi-model essay drafting
- Essay structure analyzer
- Basic improvement engine

**Reason**: Phase 3 was built first as a proof-of-concept for research capabilities.

**Impact**: Research and citation features work on existing essays, but can't create essays from scratch yet.

**Workaround**: Use external tools (ChatGPT, Claude) to create initial drafts, then use Phase 3 features to add citations/research.

**Next Steps**: Prioritize Phase 1 implementation to create end-to-end essay platform.

---

### Phase 2: Intelligence & Polish - NOT STARTED

Advanced features not yet available:
- Smart outline generator
- Grammar & clarity optimizer
- Argument analyzer & strengthener

**Workaround**: Use external tools like Grammarly, Hemingway Editor for grammar/clarity.

---

## External Dependencies

### API Keys Required

**OpenRouter API** (Optional but recommended):
- Required for: AI-powered claim detection, fact-checking, source summarization
- Fallback behavior: Uses basic heuristics without AI model

**Not Required**:
- Semantic Scholar: Free public API (no key needed)
- CrossRef: Free public API (no key needed)

### Internet Connectivity

All research and citation features require internet access for:
- Semantic Scholar API
- CrossRef DOI lookups
- OpenRouter AI models (if configured)

**Future Enhancement**: Offline mode with cached/sample data

---

## Performance Considerations

### Large Essays

**Current Limits**:
- Essay text truncated to 2000 chars for AI analysis (avoids token limits)
- Bibliography generation unlimited
- No file size restrictions

**Impact**: Very long essays (>10,000 words) may have incomplete claim detection.

**Future Fix**: Chunking strategy for large documents (Phase 2.2)

---

## Platform Compatibility

**Tested On**:
- ✅ macOS (Darwin 25.0.0)
- ✅ Python 3.12

**Expected to Work**:
- Linux (Ubuntu, Debian, etc.)
- Python 3.8+

**Known Limitations**:
- Windows: Signal-based timeouts may not work (uses SIGALRM)
- Python <3.7: Type hints not compatible

---

## Reporting New Issues

Found a bug? Please report it at:
- **GitHub**: https://github.com/swittygit/AI_Essay/issues
- **Email**: switty@level500.com

Include:
- Python version (`python --version`)
- OS version (`uname -a` or `ver`)
- Full error message
- Steps to reproduce
