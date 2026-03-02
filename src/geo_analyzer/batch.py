"""Batch scan — multi-URL × multi-keyword matrix scanning."""
import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from geo_analyzer.config import Config
from geo_analyzer.scanner import scan
from geo_analyzer.scorer import ScanReport


@dataclass
class BatchEntry:
    """Result for one URL in the batch."""
    url: str
    report: ScanReport
    avg_score: float = 0.0
    grade: str = ""

    def __post_init__(self):
        if self.report.engine_scores:
            self.avg_score = self.report.overall_score
        self.grade = self.report.grade


@dataclass
class BatchReport:
    """Aggregated batch scan results: URL × Keyword matrix."""
    urls: list[str]
    keywords: list[str]
    entries: list[BatchEntry] = field(default_factory=list)
    matrix: dict[str, dict[str, float]] = field(default_factory=dict)

    def __post_init__(self):
        if self.entries and not self.matrix:
            self._build_matrix()

    def _build_matrix(self):
        """Build URL × Keyword → average score matrix."""
        for entry in self.entries:
            url = entry.url
            self.matrix[url] = {}
            for keyword in self.keywords:
                # Get all engine scores for this keyword
                kw_scores = [
                    s.score for s in entry.report.engine_scores
                    if s.keyword == keyword
                ]
                if kw_scores:
                    self.matrix[url][keyword] = sum(kw_scores) / len(kw_scores)
                else:
                    self.matrix[url][keyword] = 0.0

    def get_url_avg(self, url: str) -> float:
        """Get average score for a URL across all keywords."""
        if url not in self.matrix:
            return 0.0
        scores = list(self.matrix[url].values())
        return sum(scores) / len(scores) if scores else 0.0

    def get_keyword_avg(self, keyword: str) -> float:
        """Get average score for a keyword across all URLs."""
        scores = [
            self.matrix[url].get(keyword, 0.0)
            for url in self.urls
            if url in self.matrix
        ]
        return sum(scores) / len(scores) if scores else 0.0


def load_urls_from_file(filepath: str) -> list[str]:
    """Load URLs from a text file, one per line.

    Skips empty lines and lines starting with #.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"URL file not found: {filepath}")

    urls = []
    for line in path.read_text().strip().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


async def batch_scan(
    urls: list[str],
    keywords: list[str],
    config: Config,
    engine_names: list[str] | None = None,
    concurrency: int = 3,
    progress_callback=None,
) -> BatchReport:
    """Run batch scan across multiple URLs and keywords.

    Args:
        urls: List of target URLs to scan
        keywords: List of keywords to query
        config: Configuration with API keys
        engine_names: Optional specific engines to use
        concurrency: Max concurrent URL scans (default: 3)
        progress_callback: Optional callable(url, done, total) for progress updates

    Returns:
        BatchReport with matrix results
    """
    semaphore = asyncio.Semaphore(concurrency)
    entries: list[BatchEntry] = []
    total = len(urls)
    done_count = 0

    async def scan_one(url: str) -> BatchEntry:
        nonlocal done_count
        async with semaphore:
            report = await scan(
                url, keywords, config, engine_names, save_history=True
            )
            done_count += 1
            if progress_callback:
                progress_callback(url, done_count, total)
            return BatchEntry(url=url, report=report)

    tasks = [scan_one(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Create an empty report for failed URLs
            empty_report = ScanReport(
                url=urls[i], keywords=keywords, engine_scores=[]
            )
            entries.append(BatchEntry(url=urls[i], report=empty_report))
        else:
            entries.append(result)

    return BatchReport(urls=urls, keywords=keywords, entries=entries)
