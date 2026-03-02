# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-02

### Added
- **Competitor comparison**: `geo-analyzer compare` to compare visibility across multiple URLs
- **History tracking**: `geo-analyzer history` to track visibility changes over time
- **Batch scanning**: scan multiple URLs in one command
- **Optimization advisor**: actionable GEO improvement suggestions after each scan
- **Storage layer**: SQLite-based local storage for scan history
- Comprehensive test suite (47 tests)

### Changed
- Bumped minimum Python version to 3.11
- Improved scoring algorithm with weighted factors
- Enhanced Rich table output with color-coded grades

## [0.1.0] - 2026-02-28

### Added
- Initial MVP release
- Three AI search engine adapters: ChatGPT, Perplexity, Gemini
- URL visibility scanning with keyword-based queries
- Visibility scoring (0-100) with letter grades (A-F)
- CLI interface with `scan` and `engines` commands
- JSON and table output formats
- API key configuration via environment variables
