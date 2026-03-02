"""Tests for batch scan module."""
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from geo_analyzer.batch import (
    BatchEntry,
    BatchReport,
    batch_scan,
    load_urls_from_file,
)
from geo_analyzer.config import Config
from geo_analyzer.scorer import EngineResult, EngineScore, ScanReport


# ── Helpers ──────────────────────────────────────────────────────────


def _make_engine_score(engine: str, keyword: str, score: int) -> EngineScore:
    """Create a mock EngineScore."""
    return EngineScore(
        engine=engine,
        keyword=keyword,
        score=score,
        mentioned=score > 0,
        cited=score >= 50,
        position="early" if score >= 60 else "middle" if score >= 30 else "not_found",
        details=f"score={score}",
        raw=EngineResult(
            engine=engine,
            query=keyword,
            response_text="mock response" if score > 0 else "",
            mentioned=score > 0,
        ),
    )


def _make_scan_report(url: str, keywords: list[str], scores: dict[str, int]) -> ScanReport:
    """Create a mock ScanReport.

    Args:
        url: Target URL
        keywords: List of keywords
        scores: Mapping of keyword -> score (uses 'chatgpt' as engine)
    """
    engine_scores = [
        _make_engine_score("chatgpt", kw, scores.get(kw, 0))
        for kw in keywords
    ]
    return ScanReport(url=url, keywords=keywords, engine_scores=engine_scores)


# ── Tests: BatchEntry ────────────────────────────────────────────────


class TestBatchEntry:
    def test_basic_creation(self):
        report = _make_scan_report("https://a.com", ["kw1"], {"kw1": 75})
        entry = BatchEntry(url="https://a.com", report=report)
        assert entry.avg_score == 75
        assert entry.grade == "B"

    def test_empty_report(self):
        report = ScanReport(url="https://a.com", keywords=["kw1"], engine_scores=[])
        entry = BatchEntry(url="https://a.com", report=report)
        assert entry.avg_score == 0
        assert entry.grade == "F"


# ── Tests: BatchReport Matrix ───────────────────────────────────────


class TestBatchReport:
    def test_matrix_building(self):
        urls = ["https://a.com", "https://b.com"]
        keywords = ["kw1", "kw2"]

        entries = [
            BatchEntry(
                url="https://a.com",
                report=_make_scan_report("https://a.com", keywords, {"kw1": 80, "kw2": 40}),
            ),
            BatchEntry(
                url="https://b.com",
                report=_make_scan_report("https://b.com", keywords, {"kw1": 60, "kw2": 90}),
            ),
        ]

        br = BatchReport(urls=urls, keywords=keywords, entries=entries)

        # Check matrix values
        assert br.matrix["https://a.com"]["kw1"] == 80
        assert br.matrix["https://a.com"]["kw2"] == 40
        assert br.matrix["https://b.com"]["kw1"] == 60
        assert br.matrix["https://b.com"]["kw2"] == 90

    def test_url_avg(self):
        urls = ["https://a.com"]
        keywords = ["kw1", "kw2"]
        entries = [
            BatchEntry(
                url="https://a.com",
                report=_make_scan_report("https://a.com", keywords, {"kw1": 80, "kw2": 40}),
            ),
        ]
        br = BatchReport(urls=urls, keywords=keywords, entries=entries)
        assert br.get_url_avg("https://a.com") == 60.0

    def test_keyword_avg(self):
        urls = ["https://a.com", "https://b.com"]
        keywords = ["kw1"]
        entries = [
            BatchEntry(
                url="https://a.com",
                report=_make_scan_report("https://a.com", keywords, {"kw1": 80}),
            ),
            BatchEntry(
                url="https://b.com",
                report=_make_scan_report("https://b.com", keywords, {"kw1": 40}),
            ),
        ]
        br = BatchReport(urls=urls, keywords=keywords, entries=entries)
        assert br.get_keyword_avg("kw1") == 60.0

    def test_empty_matrix(self):
        br = BatchReport(urls=[], keywords=[], entries=[])
        assert br.matrix == {}
        assert br.get_url_avg("https://nope.com") == 0.0
        assert br.get_keyword_avg("nope") == 0.0

    def test_missing_url_returns_zero(self):
        br = BatchReport(urls=["https://a.com"], keywords=["kw1"], entries=[])
        assert br.get_url_avg("https://nonexistent.com") == 0.0


# ── Tests: load_urls_from_file ───────────────────────────────────────


class TestLoadUrlsFromFile:
    def test_basic_file(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("https://a.com\nhttps://b.com\nhttps://c.com\n")
        result = load_urls_from_file(str(f))
        assert result == ["https://a.com", "https://b.com", "https://c.com"]

    def test_skips_comments_and_blanks(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("# This is a comment\nhttps://a.com\n\n# Another comment\nhttps://b.com\n\n")
        result = load_urls_from_file(str(f))
        assert result == ["https://a.com", "https://b.com"]

    def test_strips_whitespace(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("  https://a.com  \n  https://b.com  \n")
        result = load_urls_from_file(str(f))
        assert result == ["https://a.com", "https://b.com"]

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_urls_from_file("/nonexistent/path/urls.txt")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("")
        result = load_urls_from_file(str(f))
        assert result == []


# ── Tests: batch_scan (async, mocked) ───────────────────────────────


class TestBatchScan:
    @pytest.fixture
    def config(self):
        return Config(
            openai_api_key=None,
            perplexity_api_key=None,
            gemini_api_key=None,
        )

    def test_batch_scan_returns_batch_report(self, config):
        """batch_scan should return a BatchReport with correct structure."""
        urls = ["https://a.com", "https://b.com"]
        keywords = ["kw1", "kw2"]

        async def mock_scan(url, kws, cfg, engines=None, save_history=True):
            scores = {kw: 50 for kw in kws}
            return _make_scan_report(url, kws, scores)

        with patch("geo_analyzer.batch.scan", side_effect=mock_scan):
            result = asyncio.run(batch_scan(urls, keywords, config))

        assert isinstance(result, BatchReport)
        assert len(result.entries) == 2
        assert len(result.urls) == 2
        assert len(result.keywords) == 2
        # Check matrix is populated
        assert "https://a.com" in result.matrix
        assert "https://b.com" in result.matrix

    def test_batch_scan_concurrency_control(self, config):
        """Semaphore should limit concurrent scans."""
        max_concurrent = 0
        current_concurrent = 0

        async def mock_scan(url, kws, cfg, engines=None, save_history=True):
            nonlocal max_concurrent, current_concurrent
            current_concurrent += 1
            if current_concurrent > max_concurrent:
                max_concurrent = current_concurrent
            await asyncio.sleep(0.05)  # Simulate work
            current_concurrent -= 1
            return _make_scan_report(url, kws, {"kw1": 50})

        urls = [f"https://site{i}.com" for i in range(6)]
        keywords = ["kw1"]

        with patch("geo_analyzer.batch.scan", side_effect=mock_scan):
            asyncio.run(batch_scan(urls, keywords, config, concurrency=2))

        # With semaphore=2, max concurrent should never exceed 2
        assert max_concurrent <= 2

    def test_batch_scan_handles_errors(self, config):
        """Failed scans should produce empty entries, not crash."""
        call_count = 0

        async def mock_scan(url, kws, cfg, engines=None, save_history=True):
            nonlocal call_count
            call_count += 1
            if "fail" in url:
                raise ConnectionError("Simulated failure")
            return _make_scan_report(url, kws, {"kw1": 70})

        urls = ["https://good.com", "https://fail.com"]
        keywords = ["kw1"]

        with patch("geo_analyzer.batch.scan", side_effect=mock_scan):
            result = asyncio.run(batch_scan(urls, keywords, config))

        assert len(result.entries) == 2
        # Good URL should have score
        good_entry = [e for e in result.entries if e.url == "https://good.com"][0]
        assert good_entry.report.overall_score == 70
        # Failed URL should have empty report
        fail_entry = [e for e in result.entries if e.url == "https://fail.com"][0]
        assert fail_entry.report.overall_score == 0

    def test_batch_scan_progress_callback(self, config):
        """Progress callback should be called for each completed URL."""
        progress_calls = []

        async def mock_scan(url, kws, cfg, engines=None, save_history=True):
            return _make_scan_report(url, kws, {"kw1": 50})

        def on_progress(url, done, total):
            progress_calls.append((url, done, total))

        urls = ["https://a.com", "https://b.com", "https://c.com"]
        keywords = ["kw1"]

        with patch("geo_analyzer.batch.scan", side_effect=mock_scan):
            asyncio.run(
                batch_scan(urls, keywords, config, progress_callback=on_progress)
            )

        assert len(progress_calls) == 3
        # All should report total=3
        for _, _, total in progress_calls:
            assert total == 3


# ── Tests: Reporter (batch matrix) ──────────────────────────────────


class TestBatchReporter:
    def test_print_batch_report_no_crash(self, capsys):
        """print_batch_report should not crash with valid data."""
        from geo_analyzer.reporter import print_batch_report

        urls = ["https://a.com", "https://b.com"]
        keywords = ["kw1", "kw2"]
        entries = [
            BatchEntry(
                url="https://a.com",
                report=_make_scan_report("https://a.com", keywords, {"kw1": 85, "kw2": 45}),
            ),
            BatchEntry(
                url="https://b.com",
                report=_make_scan_report("https://b.com", keywords, {"kw1": 30, "kw2": 70}),
            ),
        ]
        br = BatchReport(urls=urls, keywords=keywords, entries=entries)

        # Should not raise
        print_batch_report(br)

    def test_export_batch_json(self):
        """export_batch_json should produce valid JSON with correct structure."""
        import json
        from geo_analyzer.reporter import export_batch_json

        urls = ["https://a.com"]
        keywords = ["kw1", "kw2"]
        entries = [
            BatchEntry(
                url="https://a.com",
                report=_make_scan_report("https://a.com", keywords, {"kw1": 80, "kw2": 40}),
            ),
        ]
        br = BatchReport(urls=urls, keywords=keywords, entries=entries)

        result = export_batch_json(br)
        data = json.loads(result)

        assert data["urls"] == ["https://a.com"]
        assert data["keywords"] == ["kw1", "kw2"]
        assert "https://a.com" in data["matrix"]
        assert data["matrix"]["https://a.com"]["kw1"]["score"] == 80.0
        assert data["matrix"]["https://a.com"]["kw1"]["grade"] == "A"
        assert data["matrix"]["https://a.com"]["kw2"]["score"] == 40.0
        assert data["matrix"]["https://a.com"]["kw2"]["grade"] == "C"
        assert "url_averages" in data
        assert "keyword_averages" in data
