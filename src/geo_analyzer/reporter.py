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
