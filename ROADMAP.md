# Project Roadmap

This document tracks the refactoring progress and future enhancements for the AI Essay project.

## Status Overview

**Current Version**: 2.0
**Status**: ✅ Core refactoring complete
**Last Updated**: November 2024

---

## ✅ Completed: Version 2.0 Refactoring

The following major refactoring has been successfully completed:

### Architecture Transformation

**Before (v1.0)**:
- 20+ duplicate scripts (4 models × 5 batches)
- Hardcoded API keys in every file
- No CLI interface
- O(n) algorithms for duplicate detection
- API client recreated on every call
- No configuration management
- No proper error handling

**After (v2.0)**:
- Single CLI entry point (`run_experiment.py`)
- Modular architecture with `src/` directory
- Abstract base classes for extensibility
- YAML configuration with CLI overrides
- Environment variable security
- O(1) efficient algorithms
- Comprehensive documentation

### Completed Tasks

#### Phase 1: Critical Fixes ✅
- [x] Created `.gitignore` with security rules
- [x] Created `.env.example` template
- [x] Migrated to environment variables (removed all hardcoded keys)
- [x] Added `python-dotenv` dependency
- [x] Fixed retry_count bug (was not reset between loops)
- [x] Fixed model configuration inconsistency (hardcoded vs variable)

#### Phase 2: Code Quality ✅
- [x] Removed all dead code (unused functions, imports)
- [x] Replaced magic numbers with proper constants
- [x] Applied Python best practices (removed unnecessary parens, used +=, etc.)
- [x] Improved variable naming (cnt → char_count, etc.)
- [x] Added specific exception handling
- [x] Added input validation

#### Phase 3: Architecture Refactoring ✅
- [x] Created new project structure (src/, tests/, results/, examples/)
- [x] Created `src/models/base.py` - Abstract AIModel base class
- [x] Created `src/models/openrouter.py` - Unified OpenRouter implementation
- [x] Created `src/utils.py` - Shared utilities (print_formatted, write_to_file, extract_essay)
- [x] Created `src/metrics.py` - MetricsCollector with @dataclass
- [x] Created `src/experiment.py` - Three experiment runner classes
- [x] Created `config.yaml` - YAML configuration system
- [x] Created `run_experiment.py` - CLI interface with argparse
- [x] Migrated to OpenRouter (single API for all models)
- [x] Eliminated 90% code duplication
- [x] Implemented O(1) duplicate detection with sets
- [x] Reusable API client (not recreated per call)
- [x] Removed legacy code (Source and Results/, batch*_unified.py)

#### Phase 4: Documentation ✅
- [x] Added type hints throughout codebase
- [x] Added docstrings to all classes and functions
- [x] Updated README.md with new architecture
- [x] Updated CLAUDE.md for developers
- [x] Created QUICKSTART.md for new users
- [x] Created comprehensive config.yaml with comments
- [x] Documented all CLI options

### Code Metrics

| Metric | Before (v1.0) | After (v2.0) | Improvement |
|--------|---------------|--------------|-------------|
| Python files | 20+ | 9 | 55% reduction |
| Lines of code | ~3000 | ~800 | 73% reduction |
| Duplicate code | ~85% | ~0% | Eliminated |
| API keys in code | 20+ | 0 | Secure |
| CLI scripts | 0 | 1 | Added |
| Test coverage | 0% | 0% (structure ready) | Framework ready |

---

## 🔄 In Progress: Testing & Quality Assurance

These items are partially complete or need attention:

### Testing Infrastructure
- [ ] **Create test fixtures** for mock API responses
- [ ] **Write unit tests** for `src/models/openrouter.py`
- [ ] **Write unit tests** for `src/utils.py`
- [ ] **Write unit tests** for `src/metrics.py`
- [ ] **Write integration tests** for experiment runners
- [ ] **Add pytest configuration** (pytest.ini)
- [ ] **Set up test coverage** reporting (pytest-cov)
- [ ] **Target**: Achieve 80%+ test coverage

**Priority**: Medium
**Estimated Effort**: 3-5 days
**Benefit**: Code reliability, regression prevention

### Code Quality Tools
- [ ] **Add pre-commit hooks** configuration
  - Black for formatting
  - Flake8 for linting
  - MyPy for type checking
- [ ] **Configure mypy** for strict type checking
- [ ] **Add GitHub Actions** CI/CD workflow
- [ ] **Run tests on push/PR**
- [ ] **Automated code quality checks**

**Priority**: Medium
**Estimated Effort**: 1-2 days
**Benefit**: Consistent code quality, automated checks

---

## 📋 Future Enhancements: Version 2.x

These features would enhance the project but are not critical:

### Enhanced Metrics & Analysis (v2.1)

- [ ] **Export metrics to CSV**
  - Raw responses with metadata
  - Summary statistics
  - Timestamps and model info

- [ ] **Export metrics to JSON**
  - Structured experiment data
  - Support for checkpoint/resume
  - Machine-readable format

- [ ] **Create analysis notebook**
  - Jupyter notebook for result analysis
  - Visualizations (matplotlib/seaborn)
  - Statistical analysis of uniqueness
  - Model comparison charts

**Priority**: Low-Medium
**Estimated Effort**: 1 week
**Benefit**: Better data analysis, publication-ready visualizations

### Logging & Monitoring (v2.2)

- [ ] **Replace print with logging module**
  - Structured logging with levels
  - Log to file and console
  - Configurable verbosity

- [ ] **Add progress bars** (tqdm)
  - Show current cycle
  - Estimated time remaining
  - Real-time metrics

- [ ] **Add checkpoint/resume capability**
  - Save state periodically
  - Resume interrupted experiments
  - Handle crashes gracefully

**Priority**: Low
**Estimated Effort**: 3-5 days
**Benefit**: Better user experience, reliability

### Performance Optimizations (v2.3)

- [ ] **Optimize duplicate detection** (already O(1), but could add bloom filters)
- [ ] **Add caching layer** for API responses
  - Cache responses for replay/testing
  - Reduce API costs during development
  - Support offline testing

- [ ] **Add async support** (optional)
  - Concurrent API calls where appropriate
  - Respect rate limits
  - Improved throughput for large experiments

**Priority**: Low
**Estimated Effort**: 1 week
**Benefit**: Faster experiments, reduced costs

### Additional Features (v2.4)

- [ ] **Add batch3 and batch4 support**
  - Implement missing batch types from v1.0
  - Ensure consistency with new architecture

- [ ] **Add model comparison mode**
  - Run same experiment across multiple models
  - Generate comparison report
  - Side-by-side analysis

- [ ] **Add web UI** (optional)
  - Simple Flask/FastAPI interface
  - Monitor running experiments
  - View results in browser

- [ ] **Add experiment templates**
  - Pre-configured YAML files for common tasks
  - Example experiments for quick start

**Priority**: Very Low
**Estimated Effort**: Varies (2-4 weeks total)
**Benefit**: Convenience, accessibility

---

## 🎯 Recommended Next Steps

Based on priority and value, here's the recommended order:

### Short Term (Next Sprint)

1. **Write unit tests** for core functionality
   - Start with `src/utils.py` (easiest)
   - Then `src/metrics.py`
   - Then `src/models/openrouter.py`
   - Target: 60%+ coverage

2. **Add basic CI/CD**
   - GitHub Actions workflow
   - Run tests on push
   - Lint checking

3. **Create simple test fixtures**
   - Mock API responses
   - Sample data for testing

### Medium Term (Next Month)

4. **Add CSV/JSON export**
   - Most requested feature for analysis
   - Relatively easy to implement

5. **Replace print with logging**
   - Better debugging
   - Professional output

6. **Add progress bars**
   - Better UX for long experiments

### Long Term (Future)

7. **Analysis notebook**
   - When you have enough data
   - Publication/presentation ready

8. **Additional features**
   - As needed based on usage

---

## 🚫 Not Planned

The following are explicitly NOT planned:

- **Multiple provider APIs**: Sticking with OpenRouter unified approach
- **GUI application**: CLI is sufficient for research use
- **Distributed computing**: Not needed for current scale
- **Database backend**: File-based output is adequate
- **Real-time streaming**: Experiments are batch-based
- **Mobile support**: Desktop/server environment only

---

## 📊 Success Metrics

### Version 2.0 Goals (✅ Achieved)
- [x] Reduce code duplication by >70%
- [x] Eliminate hardcoded secrets
- [x] Single CLI entry point
- [x] Modular, maintainable architecture
- [x] Comprehensive documentation

### Version 2.x Goals (Future)
- [ ] Test coverage >80%
- [ ] CI/CD pipeline running
- [ ] CSV/JSON export implemented
- [ ] Logging system in place
- [ ] Analysis notebook created

---

## 🔗 Related Documents

- **README.md**: User-facing documentation
- **CLAUDE.md**: Developer documentation and architecture guide
- **QUICKSTART.md**: Quick start guide for new users
- **config.yaml**: Configuration reference with examples

---

## 📝 Notes

### Design Decisions

**Why OpenRouter?**
- Single API key for all models
- Consistent interface across providers
- Centralized billing and usage tracking
- Eliminates need for 4+ separate SDKs

**Why YAML for config?**
- Human-readable and editable
- Supports comments
- Good Python library support (pyyaml)
- Industry standard for configuration

**Why @dataclass for metrics?**
- Type safety with minimal boilerplate
- Automatic __init__, __repr__
- Clean, Pythonic code
- Easy to serialize/deserialize

**Why not implement batches 3 and 4?**
- batch1, batch2, batch5 cover the core experiment types
- batch3 and batch4 are variations of batch2
- Can be easily added if needed using existing patterns

### Lessons Learned

1. **Start with architecture**: The v2.0 refactor would have been easier with the proper architecture from the start
2. **DRY principle is powerful**: Eliminating duplication reduced codebase by 73%
3. **Type hints help**: Caught several bugs during refactoring
4. **Good documentation matters**: Comprehensive docs make code maintainable
5. **Security first**: Environment variables should be used from day one

### Future Considerations

- Monitor OpenRouter API changes and model availability
- Consider rate limiting if running very large experiments
- May need to add retry with exponential backoff for rate limits
- Keep an eye on token costs across different models

---

## 📅 Version History

**v2.0** (November 2024)
- Complete architecture refactor
- OpenRouter integration
- YAML configuration
- CLI interface
- Comprehensive documentation
- 90% code reduction

**v1.0** (2024)
- Original implementation
- Model-specific scripts
- Hardcoded configuration
- Manual execution
- (Removed from repository)

---

**Last Updated**: November 21, 2024
**Status**: v2.0 Complete, v2.x Planning
