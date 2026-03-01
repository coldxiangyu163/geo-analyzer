# 🔍 GEO Analyzer

**Check your website's visibility in AI search engines.**

GEO (Generative Engine Optimization) is the next evolution of SEO — optimizing your content so AI search engines (ChatGPT, Perplexity, Gemini) can discover and cite your website.

GEO Analyzer scans your URL across multiple AI search engines and tells you:
- ✅ Whether your site is **mentioned** in AI responses
- 🔗 Whether your site is **cited with a URL**
- 📍 **Where** in the response you appear (early = better)
- 🎯 Your overall **visibility score** (0-100, grade A-F)

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

## Output Example

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
```

## Commands

```bash
# Scan a URL
geo-analyzer scan <url> -k "keyword1, keyword2"

# Use specific engines only
geo-analyzer scan <url> -k "keyword" -e chatgpt,perplexity

# JSON output
geo-analyzer scan <url> -k "keyword" -o json

# Check which engines are configured
geo-analyzer engines
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
- [ ] GEO optimization suggestions
- [ ] Competitor comparison (`geo-analyzer compare`)
- [ ] Historical tracking (`geo-analyzer history`)
- [ ] MCP Server integration
- [ ] Web dashboard

## Why GEO Matters

Traditional SEO optimizes for Google's link-based ranking. But AI search engines work differently:
- They **synthesize** answers from multiple sources
- They may **cite** your URL — or just paraphrase your content
- **Position in the AI response** matters (being mentioned first = more visibility)
- **Structured data** (JSON-LD, FAQ schema) helps AI understand your content

GEO Analyzer helps you understand and improve your visibility in this new paradigm.

## License

MIT
