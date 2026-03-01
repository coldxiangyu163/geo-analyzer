"""CLI entry point for geo-analyzer."""
import asyncio
import click
from rich.console import Console

from geo_analyzer import __version__
from geo_analyzer.config import load_config
from geo_analyzer.scanner import scan
from geo_analyzer.reporter import print_report, export_json

console = Console()


@click.group()
@click.version_option(version=__version__)
def main():
    """🔍 GEO Analyzer — Check your website's visibility in AI search engines."""
    pass


@main.command()
@click.argument("url")
@click.option("-k", "--keywords", required=True, help="Comma-separated keywords to check")
@click.option("-e", "--engines", default=None, help="Engines to use: chatgpt,perplexity,gemini (default: all)")
@click.option("-o", "--output", type=click.Choice(["table", "json"]), default="table", help="Output format")
def scan_cmd(url: str, keywords: str, engines: str | None, output: str):
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
        report = asyncio.run(scan(url, keyword_list, config, engine_list))

    if output == "json":
        click.echo(export_json(report))
    else:
        print_report(report)


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


if __name__ == "__main__":
    main()
