"""Report output — Rich terminal tables, advice, and JSON export."""
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from geo_analyzer.scorer import ScanReport
from geo_analyzer.advisor import Advice
from geo_analyzer.comparator import ComparisonReport


console = Console()


def print_report(report: ScanReport, advice_list: list[Advice] | None = None) -> None:
    """Print a beautiful terminal report."""
    # Header
    grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red bold"}
    grade_color = grade_colors.get(report.grade, "white")
    
    header = Text()
    header.append("🔍 GEO Analysis: ", style="bold")
    header.append(report.url, style="cyan underline")
    header.append("  ")
    header.append(f"Grade: {report.grade}", style=f"bold {grade_color}")
    header.append(f"  Score: {report.overall_score}/100", style="bold")
    
    console.print(Panel(header, border_style="blue"))

    # Keywords
    console.print(f"\n📝 Keywords: {', '.join(report.keywords)}\n")

    # Results table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Engine", style="cyan", width=12)
    table.add_column("Keyword", width=20)
    table.add_column("Score", justify="center", width=7)
    table.add_column("Status", width=40)

    for es in report.engine_scores:
        score_style = "green" if es.score >= 60 else "yellow" if es.score >= 30 else "red"
        
        if es.position == "error":
            score_str = "[red]ERR[/red]"
        elif not es.mentioned and es.score == 0 and not es.raw.response_text:
            score_str = "[dim]--[/dim]"
            es.details = "⚙️ API key not configured"
        else:
            score_str = f"[{score_style}]{es.score}[/{score_style}]"

        table.add_row(es.engine, es.keyword, score_str, es.details)

    console.print(table)

    # Summary
    configured = [s for s in report.engine_scores if s.raw.response_text]
    if not configured:
        console.print("\n⚠️  No engines configured. Set API keys to start scanning:")
        console.print("   export OPENAI_API_KEY=sk-...")
        console.print("   export PERPLEXITY_API_KEY=pplx-...")
        console.print("   export GEMINI_API_KEY=AI...")
    else:
        mentioned_count = sum(1 for s in configured if s.mentioned)
        cited_count = sum(1 for s in configured if s.cited)
        console.print(f"\n📊 Summary: Mentioned in {mentioned_count}/{len(configured)} queries, "
                      f"Cited in {cited_count}/{len(configured)} queries")

    # Optimization advice
    if advice_list:
        console.print("\n")
        console.print(Panel("💡 [bold]Optimization Suggestions[/bold]", border_style="yellow"))
        for adv in advice_list:
            priority_label = f"[{'red' if adv.priority == 'high' else 'yellow' if adv.priority == 'medium' else 'green'}]{adv.priority.upper()}[/]"
            console.print(f"\n  {adv.priority_icon} [{priority_label}] [bold]{adv.title}[/bold]")
            console.print(f"     {adv.description}")
            for item in adv.action_items:
                console.print(f"     → {item}")

    console.print()


def export_json(report: ScanReport, advice_list: list[Advice] | None = None) -> str:
    """Export report as JSON string."""
    data = {
        "url": report.url,
        "keywords": report.keywords,
        "overall_score": report.overall_score,
        "grade": report.grade,
        "engines": [
            {
                "engine": s.engine,
                "keyword": s.keyword,
                "score": s.score,
                "mentioned": s.mentioned,
                "cited": s.cited,
                "position": s.position,
                "details": s.details,
            }
            for s in report.engine_scores
        ],
    }
    if advice_list:
        data["advice"] = [
            {
                "priority": a.priority,
                "category": a.category,
                "title": a.title,
                "description": a.description,
                "action_items": a.action_items,
            }
            for a in advice_list
        ]
    return json.dumps(data, indent=2)


def print_history(records: list, url: str) -> None:
    """Print scan history as a Rich table.
    
    Args:
        records: List of ScanRecord objects from storage.py
        url: The URL being queried
    """
    from rich.text import Text as RichText

    header = RichText()
    header.append("📜 Scan History: ", style="bold")
    header.append(url, style="cyan underline")
    console.print(Panel(header, border_style="blue"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Date", style="dim", width=20)
    table.add_column("Engine", style="cyan", width=12)
    table.add_column("Keyword", width=20)
    table.add_column("Score", justify="center", width=7)
    table.add_column("Grade", justify="center", width=7)
    table.add_column("Mentioned", justify="center", width=10)
    table.add_column("Cited", justify="center", width=8)
    table.add_column("Position", width=10)

    for r in records:
        score_style = "green" if r.score >= 60 else "yellow" if r.score >= 30 else "red"
        grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red bold"}
        grade_style = grade_colors.get(r.grade, "white")

        # Format datetime for display
        display_date = r.scanned_at[:19].replace("T", " ") if r.scanned_at else "N/A"

        table.add_row(
            display_date,
            r.engine,
            r.keyword,
            f"[{score_style}]{r.score}[/{score_style}]",
            f"[{grade_style}]{r.grade}[/{grade_style}]",
            "✅" if r.mentioned else "❌",
            "🔗" if r.cited else "—",
            r.position,
        )

    console.print(table)
    console.print(f"\n  Total records: {len(records)}\n")


def print_trend(trend) -> None:
    """Print trend analysis with ASCII chart.
    
    Args:
        trend: TrendResult object from storage.py
    """
    from rich.text import Text as RichText

    # Header
    header = RichText()
    header.append("📈 Trend Analysis: ", style="bold")
    header.append(trend.url, style="cyan underline")
    if trend.keyword:
        header.append(f"  keyword: {trend.keyword}", style="dim")
    console.print(Panel(header, border_style="blue"))

    # Summary
    trend_colors = {"up": "green", "down": "red", "stable": "yellow"}
    trend_color = trend_colors.get(trend.trend_direction, "white")
    
    console.print(f"\n  Total scans: {trend.total_scans}")
    console.print(f"  Latest score: [bold]{trend.latest_score}[/bold] (Grade: {trend.latest_grade})")
    console.print(f"  Previous score: {trend.previous_score} (Grade: {trend.previous_grade})")
    change_str = f"+{trend.score_change}" if trend.score_change > 0 else str(trend.score_change)
    console.print(f"  Change: [{trend_color}]{trend.trend_icon} {change_str}[/{trend_color}]")

    # ASCII trend chart
    if len(trend.history) >= 2:
        console.print(f"\n  [bold]Score Trend[/bold] (last {len(trend.history)} sessions):\n")
        _print_ascii_chart(trend.history)

    console.print()


def _print_ascii_chart(history: list[tuple[str, int, str]], width: int = 50, height: int = 10) -> None:
    """Print a simple ASCII line chart of score history.
    
    Args:
        history: List of (scanned_at, avg_score, grade), most recent first
        width: Chart width in characters
        height: Chart height in rows
    """
    # Reverse so oldest is on the left
    data = list(reversed(history))
    scores = [s[1] for s in data]
    
    min_score = max(0, min(scores) - 5)
    max_score = min(100, max(scores) + 5)
    score_range = max_score - min_score if max_score != min_score else 1

    # Build chart grid
    chart_width = min(width, len(scores) * 4)
    
    for row in range(height, -1, -1):
        threshold = min_score + (score_range * row / height)
        label = f"  {int(threshold):3d} │"
        line = ""
        
        for i, score in enumerate(scores):
            normalized = (score - min_score) / score_range * height
            if abs(normalized - row) < 0.5:
                line += " ● "
            elif normalized > row:
                line += " │ "
            else:
                line += "   "
        
        console.print(f"{label}{line}")
    
    # X-axis
    console.print(f"      └{'───' * len(scores)}")
    
    # Date labels (show first and last)
    if data:
        first_date = data[0][0][:10]
        last_date = data[-1][0][:10]
        padding = max(0, len(scores) * 3 - len(first_date) - len(last_date))
        console.print(f"       {first_date}{' ' * padding}{last_date}")


def print_comparison_report(comparison: ComparisonReport) -> None:
    """Print a side-by-side comparison report."""
    # Header
    header = Text()
    header.append("⚔️  GEO Competitor Comparison", style="bold")
    console.print(Panel(header, border_style="blue"))

    console.print(f"\n📝 Keywords: {', '.join(comparison.keywords)}\n")

    # URLs with scores
    grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red bold"}

    gc1 = grade_colors.get(comparison.report1.grade, "white")
    gc2 = grade_colors.get(comparison.report2.grade, "white")
    console.print(f"  🟢 Your site:    [cyan]{comparison.url1}[/cyan]  "
                  f"[{gc1}]{comparison.report1.grade}[/{gc1}] ({comparison.report1.overall_score}/100)")
    console.print(f"  🔴 Competitor:   [cyan]{comparison.url2}[/cyan]  "
                  f"[{gc2}]{comparison.report2.grade}[/{gc2}] ({comparison.report2.overall_score}/100)")
    console.print()

    # Metrics comparison table
    table = Table(show_header=True, header_style="bold magenta", title="📊 Side-by-Side Comparison")
    table.add_column("Metric", style="bold", width=18)
    table.add_column("Your Site", justify="center", width=14)
    table.add_column("Competitor", justify="center", width=14)
    table.add_column("Diff", justify="center", width=10)
    table.add_column("Result", justify="center", width=10)

    for m in comparison.metrics:
        # Color coding: green=leading, red=behind, yellow=tie
        if m.winner == "url1":
            diff_str = f"[green]+{m.diff}[/green]" if isinstance(m.diff, (int, float)) and m.diff != 0 else ""
            result_str = "[green]✅ Lead[/green]"
            v1_str = f"[green]{m.url1_value}[/green]"
            v2_str = f"[red]{m.url2_value}[/red]"
        elif m.winner == "url2":
            diff_str = f"[red]{m.diff}[/red]" if isinstance(m.diff, (int, float)) and m.diff != 0 else ""
            result_str = "[red]❌ Behind[/red]"
            v1_str = f"[red]{m.url1_value}[/red]"
            v2_str = f"[green]{m.url2_value}[/green]"
        else:
            diff_str = "[yellow]0[/yellow]"
            result_str = "[yellow]➖ Tie[/yellow]"
            v1_str = f"[yellow]{m.url1_value}[/yellow]"
            v2_str = f"[yellow]{m.url2_value}[/yellow]"

        table.add_row(m.label, v1_str, v2_str, diff_str, result_str)

    console.print(table)

    # Competitive analysis
    if comparison.advantages:
        console.print("\n💪 [bold green]Your Advantages:[/bold green]")
        for adv in comparison.advantages:
            console.print(f"   ✅ {adv}")

    if comparison.disadvantages:
        console.print("\n⚠️  [bold red]Areas to Improve:[/bold red]")
        for dis in comparison.disadvantages:
            console.print(f"   ❌ {dis}")

    if not comparison.advantages and not comparison.disadvantages:
        console.print("\n[yellow]Both sites have similar AI search visibility.[/yellow]")

    console.print()


def export_comparison_json(comparison: ComparisonReport) -> str:
    """Export comparison report as JSON string."""
    data = {
        "url1": comparison.url1,
        "url2": comparison.url2,
        "keywords": comparison.keywords,
        "url1_score": comparison.report1.overall_score,
        "url1_grade": comparison.report1.grade,
        "url2_score": comparison.report2.overall_score,
        "url2_grade": comparison.report2.grade,
        "metrics": [
            {
                "label": m.label,
                "url1_value": m.url1_value,
                "url2_value": m.url2_value,
                "diff": m.diff,
                "winner": m.winner,
            }
            for m in comparison.metrics
        ],
        "advantages": comparison.advantages,
        "disadvantages": comparison.disadvantages,
    }
    return json.dumps(data, indent=2)


# ── Batch / Matrix Reports ──────────────────────────────────────────


def _score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    elif score >= 20:
        return "D"
    else:
        return "F"


def _grade_style(grade: str) -> str:
    """Return Rich style string for a grade (color-coded)."""
    return {
        "A": "bold green",
        "B": "green",
        "C": "yellow",
        "D": "rgb(255,165,0)",   # orange
        "F": "bold red",
    }.get(grade, "white")


def print_batch_report(batch_report) -> None:
    """Print a URL × Keyword matrix table with color-coded grades.

    Args:
        batch_report: BatchReport from batch.py
    """
    from geo_analyzer.batch import BatchReport  # avoid circular at module level

    header = Text()
    header.append("📋 Batch Scan Results", style="bold")
    header.append(f"  ({len(batch_report.urls)} URLs × {len(batch_report.keywords)} keywords)", style="dim")
    console.print(Panel(header, border_style="blue"))
    console.print()

    # Build matrix table: rows = URLs, columns = keywords + avg
    table = Table(show_header=True, header_style="bold magenta", title="URL × Keyword Score Matrix")
    table.add_column("URL", style="cyan", min_width=20, max_width=40, no_wrap=True)

    for kw in batch_report.keywords:
        table.add_column(kw, justify="center", min_width=8)

    table.add_column("Avg", justify="center", min_width=8, style="bold")
    table.add_column("Grade", justify="center", min_width=7, style="bold")

    for url in batch_report.urls:
        row_cells: list[str] = []
        # Truncate URL for display
        display_url = url if len(url) <= 38 else url[:35] + "..."
        row_cells.append(display_url)

        for kw in batch_report.keywords:
            score = batch_report.matrix.get(url, {}).get(kw, 0.0)
            grade = _score_to_grade(score)
            style = _grade_style(grade)
            row_cells.append(f"[{style}]{int(score)} ({grade})[/{style}]")

        avg = batch_report.get_url_avg(url)
        avg_grade = _score_to_grade(avg)
        avg_style = _grade_style(avg_grade)
        row_cells.append(f"[{avg_style}]{avg:.0f}[/{avg_style}]")
        row_cells.append(f"[{avg_style}]{avg_grade}[/{avg_style}]")

        table.add_row(*row_cells)

    # Keyword average footer row
    footer_cells: list[str] = ["[bold]Keyword Avg[/bold]"]
    for kw in batch_report.keywords:
        kw_avg = batch_report.get_keyword_avg(kw)
        kw_grade = _score_to_grade(kw_avg)
        kw_style = _grade_style(kw_grade)
        footer_cells.append(f"[{kw_style}]{kw_avg:.0f}[/{kw_style}]")
    # Overall average
    all_scores = [
        batch_report.matrix.get(u, {}).get(k, 0.0)
        for u in batch_report.urls
        for k in batch_report.keywords
    ]
    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0
    o_grade = _score_to_grade(overall)
    o_style = _grade_style(o_grade)
    footer_cells.append(f"[{o_style}]{overall:.0f}[/{o_style}]")
    footer_cells.append(f"[{o_style}]{o_grade}[/{o_style}]")
    table.add_row(*footer_cells, end_section=True)

    console.print(table)

    # Legend
    console.print("\n  [bold]Grade Legend:[/bold]  "
                  "[bold green]A[/bold green]≥80  "
                  "[green]B[/green]≥60  "
                  "[yellow]C[/yellow]≥40  "
                  "[rgb(255,165,0)]D[/rgb(255,165,0)]≥20  "
                  "[bold red]F[/bold red]<20")
    console.print()


def export_batch_json(batch_report) -> str:
    """Export batch report as JSON string.

    Args:
        batch_report: BatchReport from batch.py

    Returns:
        Pretty-printed JSON string
    """
    data = {
        "urls": batch_report.urls,
        "keywords": batch_report.keywords,
        "matrix": {},
        "url_averages": {},
        "keyword_averages": {},
    }

    for url in batch_report.urls:
        data["matrix"][url] = {}
        for kw in batch_report.keywords:
            score = batch_report.matrix.get(url, {}).get(kw, 0.0)
            data["matrix"][url][kw] = {
                "score": round(score, 1),
                "grade": _score_to_grade(score),
            }
        avg = batch_report.get_url_avg(url)
        data["url_averages"][url] = {
            "score": round(avg, 1),
            "grade": _score_to_grade(avg),
        }

    for kw in batch_report.keywords:
        kw_avg = batch_report.get_keyword_avg(kw)
        data["keyword_averages"][kw] = {
            "score": round(kw_avg, 1),
            "grade": _score_to_grade(kw_avg),
        }

    return json.dumps(data, indent=2)


def _score_to_grade(score: float) -> str:
    """Convert a numeric score to a letter grade."""
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    elif score >= 20:
        return "D"
    else:
        return "F"


def _grade_style(grade: str) -> str:
    """Return Rich style string for a grade."""
    styles = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red bold"}
    return styles.get(grade, "white")


def _score_cell(score: float) -> str:
    """Format a score as a colored cell with grade."""
    grade = _score_to_grade(score)
    style = _grade_style(grade)
    return f"[{style}]{score:.0f} ({grade})[/{style}]"


def print_batch_report(batch_report) -> None:
    """Print a batch scan matrix report.

    Args:
        batch_report: BatchReport object from batch.py
    """
    from geo_analyzer.batch import BatchReport

    # Header
    header = Text()
    header.append("📊 GEO Batch Scan Report", style="bold")
    header.append(f"  ({len(batch_report.urls)} URLs × {len(batch_report.keywords)} keywords)", style="dim")
    console.print(Panel(header, border_style="blue"))

    console.print(f"\n📝 Keywords: {', '.join(batch_report.keywords)}\n")

    # Matrix table: URL × Keyword
    table = Table(show_header=True, header_style="bold magenta", title="URL × Keyword Visibility Matrix")
    table.add_column("URL", style="cyan", width=35, no_wrap=True)

    for kw in batch_report.keywords:
        table.add_column(kw, justify="center", width=14)

    table.add_column("Avg", justify="center", width=10, style="bold")

    for url in batch_report.urls:
        row = [url if len(url) <= 35 else url[:32] + "..."]
        for kw in batch_report.keywords:
            score = batch_report.matrix.get(url, {}).get(kw, 0.0)
            row.append(_score_cell(score))
        # URL average
        avg = batch_report.get_url_avg(url)
        row.append(_score_cell(avg))
        table.add_row(*row)

    # Keyword averages footer row
    footer_row = ["[bold]Avg by Keyword[/bold]"]
    for kw in batch_report.keywords:
        avg = batch_report.get_keyword_avg(kw)
        footer_row.append(_score_cell(avg))
    # Overall average
    all_scores = [
        batch_report.matrix[url][kw]
        for url in batch_report.urls
        if url in batch_report.matrix
        for kw in batch_report.keywords
        if kw in batch_report.matrix.get(url, {})
    ]
    overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0
    footer_row.append(_score_cell(overall_avg))
    table.add_row(*footer_row)

    console.print(table)

    # Per-URL summary
    console.print("\n📋 [bold]Per-URL Summary:[/bold]\n")
    for entry in batch_report.entries:
        grade = entry.grade
        style = _grade_style(grade)
        console.print(
            f"  [{style}]{grade}[/{style}] {entry.avg_score:3d}/100  [cyan]{entry.url}[/cyan]"
        )

    console.print()

