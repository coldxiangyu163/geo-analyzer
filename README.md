# 🔍 GEO Analyzer

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/github/license/coldxiangyu163/geo-analyzer)
![Tests](https://img.shields.io/badge/tests-65%20passed-brightgreen)
[![PyPI version](https://img.shields.io/pypi/v/geo-analyzer)](https://pypi.org/project/geo-analyzer/)

**Check your website's visibility in AI search engines.**

GEO (Generative Engine Optimization) is the next evolution of SEO — optimizing your content so AI search engines (ChatGPT, Perplexity, Gemini) can discover and cite your website.

GEO Analyzer scans your URL across multiple AI search engines and tells you:
- ✅ Whether your site is **mentioned** in AI responses
- 🔗 Whether your site is **cited with a URL**
- 📍 **Where** in the response you appear (early = better)
- 🎯 Your overall **visibility score** (0-100, grade A-F)

## Why GEO?

> Traditional SEO is no longer enough. The way people search is fundamentally changing.

In 2025, **40%+ of information queries** start in AI search engines like ChatGPT, Perplexity, and Gemini instead of Google. These AI engines don't return a list of 10 blue links — they **synthesize a single answer** from multiple sources, and your site may or may not be included.

Here's why traditional SEO falls short in the AI era:

| | Traditional SEO | GEO (AI Search) |
|---|---|---|
| **How it works** | Ranks pages by backlinks, keywords, authority | AI reads & synthesizes content from many sources |
| **What users see** | List of 10 links — user clicks through | A single generated answer — user may never click |
| **Citation** | Your URL appears as a search result | Your URL may be cited inline — or not at all |
| **Position** | Page 1 rank #1-#10 | Early/middle/late mention in AI response |
| **Optimization** | Meta tags, backlinks, keyword density | Structured data, factual authority, clear claims |

**The problem**: You can rank #1 on Google but be completely invisible to ChatGPT. GEO Analyzer tells you exactly where you stand in AI search — and how to improve.

## Quick Start

```bash
pip install geo-analyzer

# Set at least one API key
export OPENAI_API_KEY=sk-...
export PERPLEXITY_API_KEY=pplx-...
export GEMINI_API_KEY=AI...

# Scan your website
geo-analyzer scan https://yoursite.com -k "your product, your brand"
```

## CLI Usage Examples

### 🔍 `scan` — Check AI Visibility

```bash
$ geo-analyzer scan https://promptvault.dev -k "AI art prompts, prompt gallery"
```

**Expected output:**

```
🔍 GEO Analysis: https://promptvault.dev    Grade: B  Score: 62/100

📝 Keywords: AI art prompts, prompt gallery

┌─────────────┬──────────────────┬───────┬──────────────────────────────────────┐
│ Engine      │ Keyword          │ Score │ Status                               │
├─────────────┼──────────────────┼───────┼──────────────────────────────────────┤
│ ChatGPT     │ AI art prompts   │  75   │ ✅ Mentioned | 🔗 Cited | 📍 early  │
│ ChatGPT     │ prompt gallery   │  55   │ ✅ Mentioned | ⚠️ No URL | 📍 middle│
│ Perplexity  │ AI art prompts   │  80   │ ✅ Mentioned | 🔗 Cited | 📍 early  │
│ Perplexity  │ prompt gallery   │  30   │ ✅ Mentioned | ⚠️ No URL | 📍 late  │
│ Gemini      │ AI art prompts   │  55   │ ✅ Mentioned | 🔗 Cited | 📍 middle │
│ Gemini      │ prompt gallery   │   0   │ ❌ Not mentioned                     │
└─────────────┴──────────────────┴───────┴──────────────────────────────────────┘

📊 Summary: Mentioned in 5/6 queries, Cited in 3/6 queries

💡 Suggestions:
  1. Add FAQ schema markup to improve Gemini visibility
  2. Include more direct claims about "prompt gallery" for citation
  3. Add JSON-LD structured data for better AI comprehension
```

### ⚔️ `compare` — Competitor Comparison

```bash
$ geo-analyzer compare https://promptvault.dev https://competitor.com -k "AI art prompts"
```

**Expected output:**

```
⚔️  Competitor Comparison: "AI art prompts"

┌─────────────┬──────────────────────────┬──────────────────────────┐
│ Engine      │ promptvault.dev          │ competitor.com           │
├─────────────┼──────────────────────────┼──────────────────────────┤
│ ChatGPT     │ 🟢 75  Cited, early     │ 🟡 40  Mentioned, late  │
│ Perplexity  │ 🟢 80  Cited, early     │ 🟢 70  Cited, middle    │
│ Gemini      │ 🟡 55  Cited, middle    │ 🔴  0  Not mentioned    │
├─────────────┼──────────────────────────┼──────────────────────────┤
│ Average     │ 🏆 70  Grade: B         │    37  Grade: D          │
└─────────────┴──────────────────────────┴──────────────────────────┘

✅ You lead on 3/3 engines for "AI art prompts"
```

### 📈 `history` — Track Visibility Over Time

```bash
$ geo-analyzer history https://promptvault.dev -k "AI art prompts" --trend
```

**Expected output:**

```
📈 Visibility History: https://promptvault.dev — "AI art prompts"

┌────────────┬───────┬───────┬────────┐
│ Date       │ Score │ Grade │ Trend  │
├────────────┼───────┼───────┼────────┤
│ 2026-02-28 │  45   │  C    │   —    │
│ 2026-03-01 │  58   │  C    │  ↑ 13  │
│ 2026-03-02 │  62   │  B    │  ↑  4  │
└────────────┴───────┴───────┴────────┘

📊 Trend: +17 points over 3 scans (↑ improving)
💡 Your structured data changes on 03-01 correlated with the biggest jump.
```

## All Commands

```bash
# Scan a URL
geo-analyzer scan <url> -k "keyword1, keyword2"

# Use specific engines only
geo-analyzer scan <url> -k "keyword" -e chatgpt,perplexity

# JSON output
geo-analyzer scan <url> -k "keyword" -o json

# Compare two competing URLs
geo-analyzer compare <url1> <url2> -k "keyword1, keyword2"

# View scan history & trends
geo-analyzer history <url>
geo-analyzer history <url> -k "keyword" --trend

# Batch scan: multi-URL × multi-keyword matrix
geo-analyzer batch -u "url1,url2" -k "kw1,kw2"
geo-analyzer batch -f urls.txt -k "kw1,kw2" -o json

# Check which engines are configured
geo-analyzer engines
```

## Architecture

```
geo_analyzer/
├── cli.py            # Click-based CLI entry point (scan, compare, history, batch, engines)
├── scanner.py        # Core scanning orchestrator — dispatches queries to engines
├── scorer.py         # Scoring algorithm: mention + citation + position + accuracy → 0-100
├── reporter.py       # Rich-powered terminal output (tables, colors, grades)
├── advisor.py        # GEO optimization suggestions based on scan results
├── comparator.py     # Side-by-side competitor comparison logic
├── storage.py        # SQLite-based local storage for scan history & trends
├── batch.py          # Multi-URL × multi-keyword batch scanning
├── config.py         # API key management & engine configuration
├── engines/
│   ├── base.py       # Abstract base class for engine adapters
│   ├── chatgpt.py    # OpenAI ChatGPT adapter (GPT-4o + web browsing)
│   ├── perplexity.py # Perplexity API adapter (with source citations)
│   └── gemini.py     # Google Gemini adapter (Gemini Pro)
└── __main__.py       # `python -m geo_analyzer` support
```

**Data flow:**

```
User CLI Input → Scanner → Engine Adapters → Raw AI Responses
                                                    ↓
              Reporter ← Scorer ← Response Analysis (mention/cite/position)
                 ↓            ↓
            Terminal Output   Storage (SQLite) → History & Trends
                              ↓
                          Advisor → Optimization Suggestions
```

## API Keys

| Engine | Environment Variable | Get Key |
|--------|---------------------|---------|
| ChatGPT | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| Perplexity | `PERPLEXITY_API_KEY` | [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) |
| Gemini | `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) |

## Scoring

Each query is scored 0-100:

| Factor | Points | Description |
|--------|--------|-------------|
| Mentioned | 30 | Is your site mentioned in the AI response? |
| Cited | 25 | Is there a direct URL link to your site? |
| Position | 25 | Where? Early (25) > Middle (15) > Late (5) |
| Accuracy | 20 | How accurately is your site described? |

**Grades**: A (80+) · B (60-79) · C (40-59) · D (20-39) · F (<20)

## Roadmap

- [x] CLI skeleton + scoring algorithm
- [x] ChatGPT, Perplexity, Gemini engine adapters
- [x] GEO optimization suggestions
- [x] Competitor comparison (`geo-analyzer compare`)
- [x] Historical tracking (`geo-analyzer history`)
- [x] Batch scanning (`geo-analyzer batch`)
- [ ] MCP Server integration
- [ ] Web dashboard

## License

MIT
