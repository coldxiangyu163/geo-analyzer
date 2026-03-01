"""Tests for competitor comparison module."""
import pytest
from geo_analyzer.scorer import EngineResult, EngineScore, ScanReport
from geo_analyzer.comparator import (
    ComparisonMetric,
    ComparisonReport,
    _compute_metrics,
    _analyze_competitive_position,
)


def _make_engine_score(
    engine="chatgpt", keyword="test", score=50,
    mentioned=True, cited=False, position="middle",
    response_text="some response",
):
    raw = EngineResult(
        engine=engine, query=keyword,
        response_text=response_text,
        mentioned=mentioned, cited=cited, position=position,
    )
    return EngineScore(
        engine=engine, keyword=keyword, score=score,
        mentioned=mentioned, cited=cited, position=position,
        details="test", raw=raw,
    )


def _make_report(url, scores):
    return ScanReport(url=url, keywords=["test"], engine_scores=scores)


class TestComputeMetrics:
    def test_url1_wins_on_score(self):
        r1 = _make_report("a.com", [_make_engine_score(score=80)])
        r2 = _make_report("b.com", [_make_engine_score(score=40)])
        metrics = _compute_metrics(r1, r2)
        vis = next(m for m in metrics if m.label == "Visibility Score")
        assert vis.winner == "url1"
        assert vis.diff == 40

    def test_url2_wins_on_score(self):
        r1 = _make_report("a.com", [_make_engine_score(score=20)])
        r2 = _make_report("b.com", [_make_engine_score(score=70)])
        metrics = _compute_metrics(r1, r2)
        vis = next(m for m in metrics if m.label == "Visibility Score")
        assert vis.winner == "url2"
        assert vis.diff == -50

    def test_tie_score(self):
        r1 = _make_report("a.com", [_make_engine_score(score=50)])
        r2 = _make_report("b.com", [_make_engine_score(score=50)])
        metrics = _compute_metrics(r1, r2)
        vis = next(m for m in metrics if m.label == "Visibility Score")
        assert vis.winner == "tie"
        assert vis.diff == 0

    def test_mention_count(self):
        r1 = _make_report("a.com", [
            _make_engine_score(mentioned=True),
            _make_engine_score(engine="perplexity", mentioned=True),
        ])
        r2 = _make_report("b.com", [
            _make_engine_score(mentioned=True),
            _make_engine_score(engine="perplexity", mentioned=False),
        ])
        metrics = _compute_metrics(r1, r2)
        mentions = next(m for m in metrics if m.label == "Times Mentioned")
        assert mentions.url1_value == 2
        assert mentions.url2_value == 1
        assert mentions.winner == "url1"

    def test_citation_count(self):
        r1 = _make_report("a.com", [_make_engine_score(cited=True)])
        r2 = _make_report("b.com", [_make_engine_score(cited=False)])
        metrics = _compute_metrics(r1, r2)
        cites = next(m for m in metrics if m.label == "Times Cited")
        assert cites.url1_value == 1
        assert cites.url2_value == 0
        assert cites.winner == "url1"

    def test_early_position(self):
        r1 = _make_report("a.com", [_make_engine_score(position="early")])
        r2 = _make_report("b.com", [_make_engine_score(position="late")])
        metrics = _compute_metrics(r1, r2)
        early = next(m for m in metrics if m.label == "Early Positions")
        assert early.url1_value == 1
        assert early.url2_value == 0

    def test_engine_coverage(self):
        r1 = _make_report("a.com", [
            _make_engine_score(engine="chatgpt", mentioned=True),
            _make_engine_score(engine="perplexity", mentioned=True),
        ])
        r2 = _make_report("b.com", [
            _make_engine_score(engine="chatgpt", mentioned=True),
            _make_engine_score(engine="perplexity", mentioned=False),
        ])
        metrics = _compute_metrics(r1, r2)
        cov = next(m for m in metrics if m.label == "Engine Coverage")
        assert cov.url1_value == 2
        assert cov.url2_value == 1


class TestCompetitivePosition:
    def test_strong_lead(self):
        r1 = _make_report("a.com", [_make_engine_score(score=90)])
        r2 = _make_report("b.com", [_make_engine_score(score=30)])
        adv, disadv = _analyze_competitive_position("a.com", "b.com", r1, r2)
        assert any("Strong" in a for a in adv)
        assert len(disadv) == 0 or not any("gap" in d.lower() for d in disadv)

    def test_significant_gap(self):
        r1 = _make_report("a.com", [_make_engine_score(score=20)])
        r2 = _make_report("b.com", [_make_engine_score(score=80)])
        adv, disadv = _analyze_competitive_position("a.com", "b.com", r1, r2)
        assert any("gap" in d.lower() or "deficit" in d.lower() for d in disadv)

    def test_neither_visible(self):
        r1 = _make_report("a.com", [_make_engine_score(score=0, mentioned=False, response_text="")])
        r2 = _make_report("b.com", [_make_engine_score(score=0, mentioned=False, response_text="")])
        adv, disadv = _analyze_competitive_position("a.com", "b.com", r1, r2)
        assert any("Neither" in d for d in disadv)

    def test_citation_advantage(self):
        r1 = _make_report("a.com", [_make_engine_score(cited=True)])
        r2 = _make_report("b.com", [_make_engine_score(cited=False)])
        adv, disadv = _analyze_competitive_position("a.com", "b.com", r1, r2)
        assert any("citation" in a.lower() for a in adv)


class TestComparisonReport:
    def test_auto_computes_metrics(self):
        r1 = _make_report("a.com", [_make_engine_score(score=70)])
        r2 = _make_report("b.com", [_make_engine_score(score=40)])
        report = ComparisonReport(
            url1="a.com", url2="b.com", keywords=["test"],
            report1=r1, report2=r2,
        )
        assert len(report.metrics) > 0
        assert len(report.advantages) > 0 or len(report.disadvantages) > 0
