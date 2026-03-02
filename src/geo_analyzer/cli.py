"""CLI entry point for geo-analyzer."""
import asyncio
import click
from rich.console import Console

from geo_analyzer import __version__
from geo_analyzer.config import load_config
from geo_analyzer.scanner import scan
from geo_analyzer.advisor import generate_advice
from geo_analyzer.reporter import (
    print_report, export_json,
    print_comparison_report, export_comparison_json,
    print_batch_report, export_batch_json,
)
from geo_analyzer.comparator import compare_urls

console = Console()


@click.group()
@click.version_option(version=__version__)
def main():
    """🔍 GEO Analyzer — Check your website's visibility in AI search engines."""
    pass


@main.command("scan")
@click.argument("url")
@click.option("-k", "--keywords", required=True, help="Comma-separated keywords to check")
@click.option("-e", "--engines", default=None, help="Engines to use: chatgpt,perplexity,gemini (default: all)")
@click.option("-o", "--output", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.option("--advice/--no-advice", default=True, help="Show optimization suggestions (default: on)")
@click.option("--save/--no-save", default=True, help="Save scan results to history (default: on)")
def scan_cmd(url: str, keywords: str, engines: str | None, output: str, advice: bool, save: bool):
    """Scan a URL's visibility across AI search engines.
    
    Example:
        geo-analyzer scan https://example.com -k "project management,task tracking"
    """
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    engine_list = [e.strip() for e in engines.split(",")] if engines else None
    
    config = load_config()
    available = config.get_available_engines()
    
    if not available:
        console.print("[yellow]⚠️  No API keys configured. Running in demo mode.[/yellow]")
        console.print("Set environment variables to enable engines:")
        console.print("  export OPENAI_API_KEY=sk-...")
        console.print("  export PERPLEXITY_API_KEY=pplx-...")
        console.print("  export GEMINI_API_KEY=AI...\n")

    with console.status("[bold blue]Scanning AI search engines..."):
        report = asyncio.run(scan(url, keyword_list, config, engine_list, save_history=save))

    advice_list = generate_advice(report) if advice else None

    if output == "json":
        click.echo(export_json(report, advice_list))
    else:
        print_report(report, advice_list)


@main.command()
def engines():
    """List available AI search engines and their status."""
    config = load_config()
    
    console.print("\n🔍 [bold]AI Search Engines[/bold]\n")
    
    engine_info = [
        ("ChatGPT", "OPENAI_API_KEY", config.openai_api_key),
        ("Perplexity", "PERPLEXITY_API_KEY", config.perplexity_api_key),
        ("Gemini", "GEMINI_API_KEY", config.gemini_api_key),
    ]
    
    for name, env_var, key in engine_info:
        if key:
            status = f"[green]✅ Configured[/green] ({env_var}={key[:8]}...)"
        else:
            status = f"[red]❌ Not set[/red] (export {env_var}=...)"
        console.print(f"  {name:12s} {status}")
    
    console.print()


@main.command("compare")
@click.argument("your_url")
@click.argument("competitor_url")
@click.option("-k", "--keywords", required=True, help="Comma-separated keywords to check")
@click.option("-e", "--engines", default=None, help="Engines to use: chatgpt,perplexity,gemini (default: all)")
@click.option("-o", "--output", type=click.Choice(["table", "json"]), default="table", help="Output format")
def compare_cmd(your_url: str, competitor_url: str, keywords: str, engines: str | None, output: str):
    """Compare your URL vs a competitor's visibility in AI search.

    Example:
        geo-analyzer compare https://mysite.com https://competitor.com -k "keyword1,keyword2"
    """
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    engine_list = [e.strip() for e in engines.split(",")] if engines else None

    config = load_config()
    available = config.get_available_engines()

    if not available:
        console.print("[yellow]⚠️  No API keys configured. Running in demo mode.[/yellow]")

    with console.status("[bold blue]Scanning both URLs across AI search engines..."):
        comparison = asyncio.run(compare_urls(your_url, competitor_url, keyword_list, config, engine_list))

    if output == "json":
        click.echo(export_comparison_json(comparison))
    else:
        print_comparison_report(comparison)


@main.command("history")
@click.argument("url")
@click.option("-k", "--keyword", default=None, help="Filter by keyword")
@click.option("-n", "--limit", default=20, help="Max records to show (default: 20)")
@click.option("--trend", is_flag=True, default=False, help="Show score trend chart")
def history_cmd(url: str, keyword: str | None, limit: int, trend: bool):
    """View scan history and trends for a URL.
    
    Examples:
        geo-analyzer history https://example.com
        geo-analyzer history https://example.com -k "project management"
        geo-analyzer history https://example.com --trend
    """
    from geo_analyzer.storage import get_history, get_trend
    from geo_analyzer.reporter import print_history, print_trend

    if trend:
        trend_result = get_trend(url, keyword)
        if trend_result is None:
            console.print("[yellow]⚠️  No scan history found for this URL.[/yellow]")
            console.print("Run a scan first: geo-analyzer scan <url> -k <keywords>")
            return
        print_trend(trend_result)
    else:
        records = get_history(url, keyword, limit)
        if not records:
            console.print("[yellow]⚠️  No scan history found for this URL.[/yellow]")
            console.print("Run a scan first: geo-analyzer scan <url> -k <keywords>")
            return
        print_history(records, url)


@main.command("batch")
@click.option("-u", "--urls", default=None, help="Comma-separated URLs to scan")
@click.option("-f", "--file", "url_file", default=None, help="File with URLs (one per line)")
@click.option("-k", "--keywords", required=True, help="Comma-separated keywords to check")
@click.option("-e", "--engines", default=None, help="Engines to use: chatgpt,perplexity,gemini (default: all)")
@click.option("-c", "--concurrency", default=3, help="Max concurrent URL scans (default: 3)")
@click.option("-o", "--output", type=click.Choice(["table", "json"]), default="table", help="Output format")
def batch_cmd(urls: str | None, url_file: str | None, keywords: str, engines: str | None, concurrency: int, output: str):
    """Batch scan multiple URLs across multiple keywords.

    Produces a URL × Keyword visibility matrix.

    Examples:
        geo-analyzer batch -u "https://a.com,https://b.com" -k "kw1,kw2"
        geo-analyzer batch -f urls.txt -k "kw1,kw2"
        geo-analyzer batch -u "https://a.com" -k "kw1,kw2" -o json
    """
    from geo_analyzer.batch import batch_scan, load_urls_from_file

    # Parse URLs
    url_list = []
    if urls:
        url_list.extend([u.strip() for u in urls.split(",") if u.strip()])
    if url_file:
        try:
            url_list.extend(load_urls_from_file(url_file))
        except FileNotFoundError as e:
            console.print(f"[red]❌ {e}[/red]")
            raise SystemExit(1)

    if not url_list:
        console.print("[red]❌ No URLs provided. Use --urls or --file.[/red]")
        raise SystemExit(1)

    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not keyword_list:
        console.print("[red]❌ No keywords provided.[/red]")
        raise SystemExit(1)

    engine_list = [e.strip() for e in engines.split(",")] if engines else None

    config = load_config()
    available = config.get_available_engines()

    if not available:
        console.print("[yellow]⚠️  No API keys configured. Running in demo mode.[/yellow]")

    total_scans = len(url_list) * len(keyword_list)
    console.print(f"\n🔍 [bold]Batch Scan[/bold]: {len(url_list)} URLs × {len(keyword_list)} keywords = {total_scans} scan tasks\n")

    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning...", total=len(url_list))

        def on_progress(url, done, total):
            progress.update(task, completed=done, description=f"Scanned: {url[:40]}")

        batch_report = asyncio.run(
            batch_scan(url_list, keyword_list, config, engine_list, concurrency, on_progress)
        )

    if output == "json":
        click.echo(export_batch_json(batch_report))
    else:
        print_batch_report(batch_report)


@main.command("batch")
@click.option("-u", "--urls", default=None, help="Comma-separated URLs to scan")
@click.option("-f", "--file", "url_file", default=None, help="File with URLs (one per line)")
@click.option("-k", "--keywords", required=True, help="Comma-separated keywords to check")
@click.option("-e", "--engines", default=None, help="Engines to use: chatgpt,perplexity,gemini (default: all)")
@click.option("-c", "--concurrency", default=3, help="Max concurrent URL scans (default: 3)")
@click.option("-o", "--output", type=click.Choice(["table", "json"]), default="table", help="Output format")
def batch_cmd(urls: str | None, url_file: str | None, keywords: str, engines: str | None, concurrency: int, output: str):
    """Batch scan multiple URLs across multiple keywords.

    Produces a URL × Keyword visibility matrix.

    Examples:\n
        geo-analyzer batch -u "https://a.com,https://b.com" -k "kw1,kw2"\n
        geo-analyzer batch -f urls.txt -k "kw1,kw2"\n
        geo-analyzer batch -u "https://a.com" -k "kw1" -o json
    """
    from geo_analyzer.batch import batch_scan, load_urls_from_file

    # Parse URLs
    url_list = []
    if urls:
        url_list.extend([u.strip() for u in urls.split(",") if u.strip()])
    if url_file:
        try:
            url_list.extend(load_urls_from_file(url_file))
        except FileNotFoundError as e:
            console.print(f"[red]❌ {e}[/red]")
            raise SystemExit(1)

    if not url_list:
        console.print("[red]❌ No URLs provided. Use --urls or --file.[/red]")
        raise SystemExit(1)

    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not keyword_list:
        console.print("[red]❌ No keywords provided.[/red]")
        raise SystemExit(1)

    engine_list = [e.strip() for e in engines.split(",")] if engines else None

    config = load_config()
    available = config.get_available_engines()

    if not available:
        console.print("[yellow]⚠️  No API keys configured. Running in demo mode.[/yellow]")

    total_scans = len(url_list) * len(keyword_list)
    console.print(f"\n🔍 [bold]Batch Scan[/bold]: {len(url_list)} URLs × {len(keyword_list)} keywords = {total_scans} scan tasks\n")

    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning...", total=len(url_list))

        def on_progress(url, done, total):
            progress.update(task, completed=done, description=f"Scanned: {url[:40]}")

        batch_report = asyncio.run(
            batch_scan(url_list, keyword_list, config, engine_list, concurrency, on_progress)
        )

    if output == "json":
        click.echo(export_batch_json(batch_report))
    else:
        print_batch_report(batch_report)


if __name__ == "__main__":
    main()
