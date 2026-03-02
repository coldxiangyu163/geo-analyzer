# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-02

### Added
- **Competitor comparison**: `geo-analyzer compare` to compare visibility of two URLs side-by-side across all engines
- **History tracking**: `geo-analyzer history` with `--trend` flag to track visibility changes over time
- **Batch scanning**: `geo-analyzer batch` for multi-URL × multi-keyword matrix scans with `-f` file input support
- **Optimization advisor**: actionable GEO improvement suggestions after each scan (structured data, schema markup, content tips)
- **Storage layer**: SQLite-based local storage for persisting scan history and computing trends
- Comprehensive test suite (65 tests, all passing)
- PyPI packaging preparation (`pyproject.toml`, entry points, classifiers)

### Changed
- Bumped minimum Python version to 3.11
- Improved scoring algorithm with weighted factors (mention 30 + citation 25 + position 25 + accuracy 20)
- Enhanced Rich table output with color-coded grades and emoji status indicators

## [0.1.0] - 2026-02-28

### Added
- Initial MVP release
- Three AI search engine adapters: ChatGPT (GPT-4o), Perplexity, Gemini (Gemini Pro)
- URL visibility scanning with keyword-based queries
- Visibility scoring (0-100) with letter grades (A-F)
- GEO optimization suggestions based on scan results
- Report generation with Rich-powered terminal tables
- CLI interface with `scan` and `engines` commands
- JSON and table output formats
- API key configuration via environment variables
