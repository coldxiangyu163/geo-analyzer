"""Report output — Rich terminal tables, advice, and JSON export."""
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from geo_analyzer.scorer import ScanReport
from geo_analyzer.advisor import Advice


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
