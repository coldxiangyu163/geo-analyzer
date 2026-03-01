"""Competitor comparison — compare two URLs' visibility across AI search engines."""
import asyncio
from dataclasses import dataclass, field
from geo_analyzer.config import Config
from geo_analyzer.scanner import scan
from geo_analyzer.scorer import ScanReport


@dataclass
class ComparisonMetric:
    """A single comparison metric between two URLs."""
    label: str
    url1_value: float | int | str
    url2_value: float | int | str
    diff: float | int = 0
    winner: str = "tie"  # "url1", "url2", "tie"


@dataclass
class ComparisonReport:
    """Full comparison report between two URLs."""
    url1: str
    url2: str
    keywords: list[str]
    report1: ScanReport
    report2: ScanReport
    metrics: list[ComparisonMetric] = field(default_factory=list)
    advantages: list[str] = field(default_factory=list)
    disadvantages: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.metrics:
            self.metrics = _compute_metrics(self.report1, self.report2)
        if not self.advantages and not self.disadvantages:
            self.advantages, self.disadvantages = _analyze_competitive_position(
                self.url1, self.url2, self.report1, self.report2
            )


def _compute_metrics(report1: ScanReport, report2: ScanReport) -> list[ComparisonMetric]:
    """Compute comparison metrics between two scan reports."""
    metrics = []

    # Overall visibility score
    score_diff = report1.overall_score - report2.overall_score
    metrics.append(ComparisonMetric(
        label="Visibility Score",
        url1_value=report1.overall_score,
        url2_value=report2.overall_score,
        diff=score_diff,
        winner="url1" if score_diff > 0 else "url2" if score_diff < 0 else "tie",
    ))

    # Grade
    metrics.append(ComparisonMetric(
        label="Grade",
        url1_value=report1.grade,
        url2_value=report2.grade,
        diff=0,
        winner="url1" if report1.overall_score > report2.overall_score
               else "url2" if report1.overall_score < report2.overall_score
               else "tie",
    ))

    # Mentioned count
    configured1 = [s for s in report1.engine_scores if s.raw.response_text]
    configured2 = [s for s in report2.engine_scores if s.raw.response_text]
    mentioned1 = sum(1 for s in configured1 if s.mentioned)
    mentioned2 = sum(1 for s in configured2 if s.mentioned)
    mention_diff = mentioned1 - mentioned2
    metrics.append(ComparisonMetric(
        label="Times Mentioned",
        url1_value=mentioned1,
        url2_value=mentioned2,
        diff=mention_diff,
        winner="url1" if mention_diff > 0 else "url2" if mention_diff < 0 else "tie",
    ))

    # Citation count
    cited1 = sum(1 for s in configured1 if s.cited)
    cited2 = sum(1 for s in configured2 if s.cited)
    cite_diff = cited1 - cited2
    metrics.append(ComparisonMetric(
        label="Times Cited",
        url1_value=cited1,
        url2_value=cited2,
        diff=cite_diff,
        winner="url1" if cite_diff > 0 else "url2" if cite_diff < 0 else "tie",
    ))

    # Early position count (best ranking)
    early1 = sum(1 for s in configured1 if s.position == "early")
    early2 = sum(1 for s in configured2 if s.position == "early")
    early_diff = early1 - early2
    metrics.append(ComparisonMetric(
        label="Early Positions",
        url1_value=early1,
        url2_value=early2,
        diff=early_diff,
        winner="url1" if early_diff > 0 else "url2" if early_diff < 0 else "tie",
    ))

    # Engine coverage (how many unique engines mention the site)
    engines1 = set(s.engine for s in configured1 if s.mentioned)
    engines2 = set(s.engine for s in configured2 if s.mentioned)
    coverage_diff = len(engines1) - len(engines2)
    metrics.append(ComparisonMetric(
        label="Engine Coverage",
        url1_value=len(engines1),
        url2_value=len(engines2),
        diff=coverage_diff,
        winner="url1" if coverage_diff > 0 else "url2" if coverage_diff < 0 else "tie",
    ))

    return metrics


def _analyze_competitive_position(
    url1: str, url2: str,
    report1: ScanReport, report2: ScanReport,
) -> tuple[list[str], list[str]]:
    """Generate competitive advantage/disadvantage analysis."""
    advantages = []
    disadvantages = []

    score_diff = report1.overall_score - report2.overall_score

    if score_diff > 20:
        advantages.append(f"Strong visibility lead (+{score_diff} points)")
    elif score_diff > 0:
        advantages.append(f"Slight visibility lead (+{score_diff} points)")
    elif score_diff < -20:
        disadvantages.append(f"Significant visibility gap ({score_diff} points)")
    elif score_diff < 0:
        disadvantages.append(f"Slight visibility deficit ({score_diff} points)")

    configured1 = [s for s in report1.engine_scores if s.raw.response_text]
    configured2 = [s for s in report2.engine_scores if s.raw.response_text]

    # Per-engine analysis
    engines1_by_name = {}
    engines2_by_name = {}
    for s in configured1:
        engines1_by_name.setdefault(s.engine, []).append(s)
    for s in configured2:
        engines2_by_name.setdefault(s.engine, []).append(s)

    all_engines = set(engines1_by_name.keys()) | set(engines2_by_name.keys())
    for engine in sorted(all_engines):
        scores1 = engines1_by_name.get(engine, [])
        scores2 = engines2_by_name.get(engine, [])
        avg1 = sum(s.score for s in scores1) / max(len(scores1), 1)
        avg2 = sum(s.score for s in scores2) / max(len(scores2), 1)
        if avg1 > avg2 + 10:
            advantages.append(f"Stronger on {engine} ({avg1:.0f} vs {avg2:.0f})")
        elif avg2 > avg1 + 10:
            disadvantages.append(f"Weaker on {engine} ({avg1:.0f} vs {avg2:.0f})")

    # Citation advantage
    cited1 = sum(1 for s in configured1 if s.cited)
    cited2 = sum(1 for s in configured2 if s.cited)
    if cited1 > cited2:
        advantages.append(f"More URL citations ({cited1} vs {cited2})")
    elif cited2 > cited1:
        disadvantages.append(f"Fewer URL citations ({cited1} vs {cited2})")

    # If neither has any visibility
    if report1.overall_score == 0 and report2.overall_score == 0:
        advantages.clear()
        disadvantages.clear()
        disadvantages.append("Neither site is visible in AI search engines")

    return advantages, disadvantages


async def compare_urls(
    url1: str,
    url2: str,
    keywords: list[str],
    config: Config,
    engine_names: list[str] | None = None,
) -> ComparisonReport:
    """Compare two URLs' visibility across AI search engines.

    Runs scans for both URLs concurrently and produces a comparison report.

    Args:
        url1: Your website URL
        url2: Competitor website URL
        keywords: Keywords to check
        config: Configuration with API keys
        engine_names: Optional list of specific engines to use

    Returns:
        ComparisonReport with side-by-side metrics
    """
    # Run both scans concurrently
    report1, report2 = await asyncio.gather(
        scan(url1, keywords, config, engine_names),
        scan(url2, keywords, config, engine_names),
    )

    return ComparisonReport(
        url1=url1,
        url2=url2,
        keywords=keywords,
        report1=report1,
        report2=report2,
    )
