"""GEO optimization advisor — generates actionable recommendations."""
from dataclasses import dataclass, field
from geo_analyzer.scorer import ScanReport, EngineScore


@dataclass
class Advice:
    priority: str  # "high", "medium", "low"
    category: str
    title: str
    description: str
    action_items: list[str] = field(default_factory=list)

    @property
    def priority_icon(self) -> str:
        return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(self.priority, "⚪")


def generate_advice(report: ScanReport) -> list[Advice]:
    """Analyze scan results and generate optimization suggestions."""
    advice: list[Advice] = []
    
    if not report.engine_scores:
        return advice

    configured = [s for s in report.engine_scores if s.raw.response_text]
    
    # If no engines configured, give setup advice only
    if not configured:
        advice.append(Advice(
            priority="high",
            category="Setup",
            title="Configure AI Search Engine API Keys",
            description="No engines are configured. Set API keys to start analyzing your visibility.",
            action_items=[
                "export OPENAI_API_KEY=sk-... (for ChatGPT)",
                "export PERPLEXITY_API_KEY=pplx-... (for Perplexity)",
                "export GEMINI_API_KEY=AI... (for Gemini)",
            ],
        ))
        return advice

    mentioned_scores = [s for s in configured if s.mentioned]
    not_mentioned = [s for s in configured if not s.mentioned]
    cited_scores = [s for s in configured if s.cited]
    not_cited = [s for s in mentioned_scores if not s.cited]
    late_positions = [s for s in configured if s.position == "late"]

    # Not mentioned at all — most critical
    if not_mentioned:
        engines = set(s.engine for s in not_mentioned)
        keywords = set(s.keyword for s in not_mentioned)
        advice.append(Advice(
            priority="high",
            category="Visibility",
            title="Improve Discoverability in AI Search",
            description=(
                f"Your site was NOT mentioned in {len(not_mentioned)}/{len(configured)} queries "
                f"across {', '.join(engines)}. AI engines may not know about your site."
            ),
            action_items=[
                "Add JSON-LD structured data (Organization, WebSite, FAQ schemas)",
                "Create a comprehensive About page explaining what your site does",
                "Build backlinks from authoritative sources that AI engines trust",
                "Ensure your site is indexed by Google (AI engines often use web search)",
                f"Target these keywords in your content: {', '.join(list(keywords)[:5])}",
            ],
        ))

    # Mentioned but not cited
    if not_cited:
        advice.append(Advice(
            priority="high" if len(not_cited) > len(configured) // 2 else "medium",
            category="Citations",
            title="Increase URL Citation Rate",
            description=(
                f"Your site was mentioned but NOT cited with a URL in {len(not_cited)} queries. "
                "AI engines know about you but don't link to you."
            ),
            action_items=[
                "Add canonical URLs to all pages",
                "Improve internal linking structure",
                "Add a sitemap.xml and submit to search engines",
                "Create unique, authoritative content that AI engines want to reference",
                "Use descriptive, keyword-rich URLs",
            ],
        ))

    # Late position
    if late_positions:
        advice.append(Advice(
            priority="medium",
            category="Positioning",
            title="Improve Position in AI Responses",
            description=(
                f"Your site appears late in AI responses for {len(late_positions)} queries. "
                "Earlier mentions get more visibility and clicks."
            ),
            action_items=[
                "Optimize page titles and H1 tags with target keywords",
                "Put the most important information in the first paragraph",
                "Add FAQ sections that directly answer common queries",
                "Use clear, concise meta descriptions",
                "Structure content with headers that match search intent",
            ],
        ))

    # Good scores — suggest maintaining
    if report.overall_score >= 60:
        advice.append(Advice(
            priority="low",
            category="Maintenance",
            title="Maintain Your Strong AI Visibility",
            description="Your site has good AI search visibility. Focus on maintaining and expanding.",
            action_items=[
                "Monitor visibility regularly with geo-analyzer",
                "Keep content fresh and up-to-date",
                "Expand to more keywords and topics",
                "Track competitor visibility for the same keywords",
            ],
        ))

    # General GEO best practices (always include)
    advice.append(Advice(
        priority="low",
        category="Best Practices",
        title="General GEO Optimization Tips",
        description="These practices improve visibility across all AI search engines.",
        action_items=[
            "Add structured data (JSON-LD) for your content type",
            "Create an API or data feed that AI engines can consume",
            "Write content that directly answers questions (FAQ format)",
            "Build E-E-A-T signals (Experience, Expertise, Authority, Trust)",
            "Ensure fast page load times and mobile-friendliness",
        ],
    ))

    return advice
