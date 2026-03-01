"""CLI main entry point for Sentinel commands."""

import asyncio
import signal
from pathlib import Path
from typing import Annotated

import rich.table
import structlog
import typer
from rich import print as rprint
from rich.console import Console

from src.config import get_settings
from src.core.database import close_db, get_session, init_db
from src.models.entity import EntityCreate, EntityUpdate
from src.sentinel.entity_service import (
    DuplicateEntityError,
    EntityNotFoundError,
    EntityService,
)

# Configure structlog for CLI
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
console = Console()

app = typer.Typer(
    name="sentinel",
    help="TalentIntel Sentinel - OSINT-based talent intelligence monitoring",
    no_args_is_help=True,
)


def get_config_path() -> Path | None:
    """Get config file path."""
    config_path = Path("config/config.yaml")
    return config_path if config_path.exists() else None


@app.command()
def init() -> None:
    """Initialize Sentinel - create config file and database.

    Creates:
    - config/config.yaml (if not exists)
    - data/ directory
    - Database tables
    """
    rprint("[bold blue]Initializing Sentinel...[/bold blue]")

    # Create config directory
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    # Create default config if not exists
    config_path = config_dir / "config.yaml"
    if not config_path.exists():
        default_config = """# TalentIntel Configuration

# Database settings
database:
  url: "sqlite+aiosqlite:///./data/sentinel.db"
  echo: false

# GitHub API settings
github:
  # Set via SENTINEL_GITHUB_TOKEN environment variable
  # token: "your-github-token"
  api_base_url: "https://api.github.com"
  request_timeout: 30
  max_retries: 3

# Monitoring settings
monitoring:
  default_check_interval: 3600  # 1 hour
  baseline_learning_period: 14  # days

# Logging settings
logging:
  level: "INFO"
  format: "console"  # json or console

# Alert settings
alert:
  # Set via SENTINEL_ALERT_DISCORD_WEBHOOK environment variable
  # discord_webhook: "https://discord.com/api/webhooks/..."
  min_confidence: 0.7

# Application settings
app:
  debug: false
  data_dir: "./data"
"""
        config_path.write_text(default_config)
        rprint(f"[green]Created config file:[/green] {config_path}")
    else:
        rprint(f"[yellow]Config file already exists:[/yellow] {config_path}")

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    rprint(f"[green]Data directory:[/green] {data_dir}")

    # Initialize database
    async def _init_db() -> None:
        await init_db()
        await close_db()

    asyncio.run(_init_db())
    rprint("[green]Database initialized[/green]")

    rprint("\n[bold green]Sentinel initialized successfully![/bold green]")
    rprint("\nNext steps:")
    rprint("  1. Set your GitHub token: [cyan]export SENTINEL_GITHUB_TOKEN=your_token[/cyan]")
    rprint("  2. Add an entity: [cyan]sentinel add github_username --name \"Name\"[/cyan]")


@app.command()
def add(
    github_username: Annotated[
        str,
        typer.Argument(..., help="GitHub username to monitor"),
    ],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Display name for the entity"),
    ] = None,
    priority: Annotated[
        int,
        typer.Option("--priority", "-p", help="Priority (1-10, higher = more important)"),
    ] = 5,
    company: Annotated[
        str | None,
        typer.Option("--company", "-c", help="Current company"),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option("--title", "-t", help="Current job title"),
    ] = None,
    notes: Annotated[
        str | None,
        typer.Option("--notes", help="Additional notes"),
    ] = None,
) -> None:
    """Add a new entity to monitor.

    Example:
        sentinel add torvalds --name "Linus Torvalds" --priority 10
    """
    display_name = name or github_username

    async def _add_entity() -> None:
        async with get_session() as session:
            service = EntityService(session)

            entity_create = EntityCreate(
                name=display_name,
                github_username=github_username,
                current_company=company,
                current_title=title,
                priority=priority,
                notes=notes,
            )

            try:
                entity = await service.create_entity(entity_create)
                rprint(f"[green]Entity created successfully![/green]")
                rprint(f"  ID: [cyan]{entity.id}[/cyan]")
                rprint(f"  Name: [cyan]{entity.name}[/cyan]")
                rprint(f"  GitHub: [cyan]{entity.github_username}[/cyan]")
            except DuplicateEntityError as e:
                rprint(f"[red]Error: Entity with {e.field}={e.value} already exists[/red]")
                raise typer.Exit(1)

    asyncio.run(_add_entity())


@app.command("list")
def list_entities(
    active_only: Annotated[
        bool,
        typer.Option("--active-only", "-a", help="Show only active entities"),
    ] = False,
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Maximum number of entities to show"),
    ] = 50,
) -> None:
    """List all monitored entities.

    Example:
        sentinel list --active-only
    """
    async def _list_entities() -> None:
        async with get_session() as session:
            service = EntityService(session)
            entities = await service.list_entities(active_only=active_only, limit=limit)

            if not entities:
                rprint("[yellow]No entities found.[/yellow]")
                return

            table = rich.table.Table(title="Monitored Entities")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("GitHub", style="blue")
            table.add_column("State", style="magenta")
            table.add_column("Priority", justify="right")
            table.add_column("Active", justify="center")

            for entity in entities:
                active_str = "[green]Y[/green]" if entity.is_active else "[red]N[/red]"
                state_str = entity.current_state or "unknown"
                table.add_row(
                    entity.id,
                    entity.name,
                    entity.github_username or "-",
                    state_str,
                    str(entity.priority),
                    active_str,
                )

            console.print(table)
            rprint(f"\nTotal: [bold]{len(entities)}[/bold] entities")

    asyncio.run(_list_entities())


@app.command()
def status(
    entity_id: Annotated[
        str,
        typer.Argument(..., help="Entity ID to show status for"),
    ],
) -> None:
    """Show detailed status for an entity.

    Example:
        sentinel status ent_abc123
    """
    async def _show_status() -> None:
        async with get_session() as session:
            service = EntityService(session)

            try:
                entity = await service.get_entity_or_raise(entity_id)
            except EntityNotFoundError as e:
                rprint(f"[red]Error: Entity not found: {e.entity_id}[/red]")
                raise typer.Exit(1)

            # Display entity details
            rprint(f"\n[bold cyan]Entity: {entity.name}[/bold cyan]")
            rprint(f"[dim]ID: {entity.id}[/dim]\n")

            table = rich.table.Table(show_header=False, box=None)
            table.add_column("Field", style="bold")
            table.add_column("Value")

            table.add_row("GitHub", entity.github_username or "-")
            table.add_row("Twitter", entity.twitter_handle or "-")
            table.add_row("LinkedIn", entity.linkedin_url or "-")
            table.add_row("Website", entity.personal_website or "-")

            rprint("[bold]Platform Accounts[/bold]")
            console.print(table)

            rprint("\n[bold]Career Status[/bold]")
            status_table = rich.table.Table(show_header=False, box=None)
            status_table.add_column("Field", style="bold")
            status_table.add_column("Value")

            state_color = _get_state_color(entity.current_state)
            status_table.add_row(
                "Current State",
                f"[{state_color}]{entity.current_state or 'unknown'}[/{state_color}]"
            )
            status_table.add_row("Confidence", f"{entity.state_confidence:.0%}" if entity.state_confidence else "-")
            status_table.add_row("Company", entity.current_company or "-")
            status_table.add_row("Title", entity.current_title or "-")

            console.print(status_table)

            rprint("\n[bold]Monitoring[/bold]")
            monitor_table = rich.table.Table(show_header=False, box=None)
            monitor_table.add_column("Field", style="bold")
            monitor_table.add_column("Value")

            active_str = "[green]Yes[/green]" if entity.is_active else "[red]No[/red]"
            monitor_table.add_row("Active", active_str)
            monitor_table.add_row("Priority", str(entity.priority))

            if entity.tags:
                monitor_table.add_row("Tags", ", ".join(entity.tags))

            console.print(monitor_table)

            if entity.notes:
                rprint(f"\n[bold]Notes[/bold]")
                rprint(entity.notes)

            rprint(f"\n[dim]Created: {entity.created_at}[/dim]")
            rprint(f"[dim]Updated: {entity.updated_at}[/dim]")

    asyncio.run(_show_status())


def _get_state_color(state: str | None) -> str:
    """Get color for career state."""
    colors = {
        "stable": "green",
        "observing": "yellow",
        "job_hunting": "orange1",
        "interviewing": "orange3",
        "handing_over": "magenta",
        "transitioned": "blue",
        "startup_ready": "cyan",
        "sabbatical": "dim",
        "unknown": "dim",
    }
    return colors.get(state or "unknown", "white")


@app.command()
def fetch(
    entity_id: Annotated[
        str,
        typer.Argument(..., help="Entity ID to fetch data for"),
    ],
) -> None:
    """Manually trigger data fetch for an entity.

    Example:
        sentinel fetch ent_abc123
    """
    async def _fetch_entity() -> None:
        async with get_session() as session:
            service = EntityService(session)

            try:
                entity = await service.get_entity_or_raise(entity_id)
            except EntityNotFoundError as e:
                rprint(f"[red]Error: Entity not found: {e.entity_id}[/red]")
                raise typer.Exit(1)

            if not entity.github_username:
                rprint("[red]Error: Entity has no GitHub username configured[/red]")
                raise typer.Exit(1)

            rprint(f"[bold blue]Fetching data for {entity.name}...[/bold blue]")

            # Import collector
            from src.collectors.github import GitHubCollector, GitHubAPIError, NotFoundError

            collector = GitHubCollector()

            try:
                # Fetch profile
                profile, etag = await collector.fetch_profile(entity.github_username)

                if profile:
                    rprint(f"[green]Profile fetched successfully![/green]")
                    rprint(f"  Name: {profile.name}")
                    rprint(f"  Company: {profile.company}")
                    rprint(f"  Location: {profile.location}")
                    rprint(f"  Public repos: {profile.public_repos}")
                    rprint(f"  Followers: {profile.followers}")
                else:
                    rprint("[yellow]Profile not modified (using cached data)[/yellow]")

                # Fetch events
                events, _ = await collector.fetch_events(entity.github_username)
                rprint(f"[green]Fetched {len(events)} recent events[/green]")

            except NotFoundError:
                rprint(f"[red]Error: GitHub user '{entity.github_username}' not found[/red]")
                raise typer.Exit(1)
            except GitHubAPIError as e:
                rprint(f"[red]GitHub API error: {e.message}[/red]")
                raise typer.Exit(1)
            finally:
                await collector.close()

    asyncio.run(_fetch_entity())


@app.command()
def delete(
    entity_id: Annotated[
        str,
        typer.Argument(..., help="Entity ID to delete"),
    ],
    confirm: Annotated[
        bool,
        typer.Option("--confirm", "-y", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Delete an entity.

    Example:
        sentinel delete ent_abc123 --confirm
    """
    async def _delete_entity() -> None:
        async with get_session() as session:
            service = EntityService(session)

            try:
                entity = await service.get_entity_or_raise(entity_id)
            except EntityNotFoundError as e:
                rprint(f"[red]Error: Entity not found: {e.entity_id}[/red]")
                raise typer.Exit(1)

            if not confirm:
                confirm_delete = typer.confirm(
                    f"Are you sure you want to delete '{entity.name}' ({entity.id})?"
                )
                if not confirm_delete:
                    rprint("[yellow]Cancelled.[/yellow]")
                    return

            await service.delete_entity(entity_id)
            rprint(f"[green]Entity deleted: {entity.name} ({entity.id})[/green]")

    asyncio.run(_delete_entity())


@app.command()
def update(
    entity_id: Annotated[
        str,
        typer.Argument(..., help="Entity ID to update"),
    ],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Display name"),
    ] = None,
    priority: Annotated[
        int | None,
        typer.Option("--priority", "-p", help="Priority (1-10)"),
    ] = None,
    company: Annotated[
        str | None,
        typer.Option("--company", "-c", help="Current company"),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option("--title", "-t", help="Current job title"),
    ] = None,
    notes: Annotated[
        str | None,
        typer.Option("--notes", help="Additional notes"),
    ] = None,
    active: Annotated[
        bool | None,
        typer.Option("--active/--inactive", help="Set active status"),
    ] = None,
) -> None:
    """Update an entity.

    Example:
        sentinel update ent_abc123 --priority 8 --company "New Corp"
    """
    async def _update_entity() -> None:
        async with get_session() as session:
            service = EntityService(session)

            # Build update data with only non-None values
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if priority is not None:
                update_data["priority"] = priority
            if company is not None:
                update_data["current_company"] = company
            if title is not None:
                update_data["current_title"] = title
            if notes is not None:
                update_data["notes"] = notes
            if active is not None:
                update_data["is_active"] = active

            # Check if any updates provided
            if not update_data:
                rprint("[yellow]No updates provided. Use options to specify fields to update.[/yellow]")
                return

            entity_update = EntityUpdate(**update_data)

            try:
                entity = await service.update_entity(entity_id, entity_update)
                rprint(f"[green]Entity updated successfully![/green]")
                rprint(f"  ID: [cyan]{entity.id}[/cyan]")
                rprint(f"  Name: [cyan]{entity.name}[/cyan]")
            except EntityNotFoundError as e:
                rprint(f"[red]Error: Entity not found: {e.entity_id}[/red]")
                raise typer.Exit(1)

    asyncio.run(_update_entity())


# ============================================================================
# Monitor Commands
# ============================================================================

monitor_app = typer.Typer(
    name="monitor",
    help="Monitoring scheduler commands",
)
app.add_typer(monitor_app, name="monitor")


@monitor_app.command("start")
def monitor_start(
    interval: Annotated[
        int,
        typer.Option("--interval", "-i", help="Check interval in seconds"),
    ] = 3600,
) -> None:
    """Start the monitoring scheduler.

    Example:
        sentinel monitor start --interval 1800
    """
    from src.core.scheduler import get_scheduler
    from src.monitor.github_monitor import GitHubMonitor

    rprint("[bold blue]Starting monitoring scheduler...[/bold blue]")

    scheduler = get_scheduler()
    settings = get_settings()

    async def _run_monitor() -> None:
        async with get_session() as session:
            monitor = GitHubMonitor(session)

            async def monitor_job() -> None:
                rprint(f"[dim]{asyncio.get_event_loop().time()}: Running monitoring job...[/dim]")
                results = await monitor.monitor_all_active()
                success = sum(1 for r in results if r.get("status") == "success")
                rprint(f"[green]Monitoring complete: {success}/{len(results)} entities updated[/green]")

            # Add monitoring job
            scheduler.add_interval_job(
                monitor_job,
                job_id="github_monitor",
                seconds=interval,
            )

            # Start scheduler
            scheduler.start()

            rprint(f"[green]Scheduler started with {interval}s interval[/green]")
            rprint("[dim]Press Ctrl+C to stop[/dim]")

            # Run initial monitoring
            await monitor_job()

            # Keep running until interrupted
            try:
                while scheduler.is_running:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            finally:
                scheduler.stop()
                await monitor.close()

    try:
        asyncio.run(_run_monitor())
    except KeyboardInterrupt:
        rprint("\n[yellow]Scheduler stopped[/yellow]")


@monitor_app.command("status")
def monitor_status() -> None:
    """Show scheduler status.

    Example:
        sentinel monitor status
    """
    from src.core.scheduler import get_scheduler

    scheduler = get_scheduler()

    if not scheduler.is_running:
        rprint("[yellow]Scheduler is not running[/yellow]")
        return

    jobs = scheduler.get_jobs()

    rprint("[bold green]Scheduler is running[/bold green]")
    rprint(f"\nScheduled jobs: {len(jobs)}")

    if jobs:
        table = rich.table.Table()
        table.add_column("Job ID", style="cyan")
        table.add_column("Next Run", style="green")
        table.add_column("Trigger", style="yellow")

        for job in jobs:
            table.add_row(
                job["id"],
                str(job["next_run"]) if job["next_run"] else "-",
                job["trigger"],
            )

        console.print(table)


@monitor_app.command("run")
def monitor_run() -> None:
    """Run monitoring once manually.

    Example:
        sentinel monitor run
    """
    from src.monitor.github_monitor import GitHubMonitor

    async def _run_once() -> None:
        async with get_session() as session:
            monitor = GitHubMonitor(session)

            rprint("[bold blue]Running monitoring for all active entities...[/bold blue]")

            try:
                results = await monitor.monitor_all_active()

                success = sum(1 for r in results if r.get("status") == "success")
                failed = sum(1 for r in results if r.get("status") == "error")
                skipped = len(results) - success - failed

                rprint(f"\n[bold]Monitoring Complete[/bold]")
                rprint(f"  [green]Success: {success}[/green]")
                rprint(f"  [red]Failed: {failed}[/red]")
                rprint(f"  [yellow]Skipped: {skipped}[/yellow]")

            finally:
                await monitor.close()

    asyncio.run(_run_once())


# ============================================================================
# Baseline Commands
# ============================================================================

baseline_app = typer.Typer(
    name="baseline",
    help="Baseline learning commands",
)
app.add_typer(baseline_app, name="baseline")


@baseline_app.command("learn")
def baseline_learn(
    entity_id: Annotated[
        str,
        typer.Argument(..., help="Entity ID to learn baseline for"),
    ],
) -> None:
    """Learn baseline for a specific entity.

    Example:
        sentinel baseline learn ent_abc123
    """
    from src.monitor.baseline_learner import BaselineLearner

    async def _learn() -> None:
        async with get_session() as session:
            learner = BaselineLearner(session)

            rprint(f"[bold blue]Learning baseline for {entity_id}...[/bold blue]")

            baseline = await learner.learn_baseline(entity_id)

            rprint(f"[green]Baseline learned successfully![/green]")
            rprint(f"  Sample size: {baseline.get('sample_size', 0)} events")
            rprint(f"  Learning period: {baseline.get('learning_period_days', 0)} days")

            commit_pattern = baseline.get("commit_pattern", {})
            if commit_pattern.get("total_commits", 0) > 0:
                rprint(f"  Total commits: {commit_pattern.get('total_commits', 0)}")
                rprint(f"  Avg commits/day: {commit_pattern.get('avg_commits_per_day', 0)}")

            await session.commit()

    asyncio.run(_learn())


@baseline_app.command("update-all")
def baseline_update_all() -> None:
    """Update baselines for all active entities.

    Example:
        sentinel baseline update-all
    """
    from src.monitor.baseline_learner import BaselineLearner

    async def _update_all() -> None:
        async with get_session() as session:
            learner = BaselineLearner(session)

            rprint("[bold blue]Updating baselines for all active entities...[/bold blue]")

            summary = await learner.update_all_baselines()

            rprint(f"\n[bold]Baseline Update Complete[/bold]")
            rprint(f"  Total entities: {summary['total']}")
            rprint(f"  [green]Updated: {summary['updated']}[/green]")
            rprint(f"  [yellow]Skipped: {summary['skipped']}[/yellow]")
            rprint(f"  [red]Failed: {summary['failed']}[/red]")

            await session.commit()

    asyncio.run(_update_all())


# ============================================================================
# Signal Commands
# ============================================================================

signals_app = typer.Typer(
    name="signals",
    help="Signal management commands",
)
app.add_typer(signals_app, name="signals")


@signals_app.command("list")
def signals_list(
    entity_id: Annotated[
        str | None,
        typer.Option("--entity", "-e", help="Filter by entity ID"),
    ] = None,
    min_confidence: Annotated[
        float | None,
        typer.Option("--min-confidence", "-c", help="Minimum confidence threshold"),
    ] = 0.5,
    days: Annotated[
        int | None,
        typer.Option("--days", "-d", help="Only signals from last N days"),
    ] = 30,
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Maximum number of signals to show"),
    ] = 50,
) -> None:
    """List detected signals.

    Example:
        sentinel signals list --min-confidence 0.7 --days 7
    """
    from src.sentinel.signal_service import SignalService

    async def _list_signals() -> None:
        async with get_session() as session:
            service = SignalService(session)

            signals = await service.list_signals(
                entity_id=entity_id,
                min_confidence=min_confidence,
                days=days,
                limit=limit,
            )

            if not signals:
                rprint("[yellow]No signals found.[/yellow]")
                return

            table = rich.table.Table(title="Detected Signals")
            table.add_column("ID", style="dim", justify="right")
            table.add_column("Entity", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Confidence", justify="right")
            table.add_column("Description", max_width=40)
            table.add_column("Detected", style="yellow")
            table.add_column("Processed", justify="center")

            for sig in signals:
                processed_str = "[green]Y[/green]" if sig.is_processed else "[red]N[/red]"
                conf_color = "green" if sig.confidence >= 0.7 else "yellow" if sig.confidence >= 0.5 else "dim"
                table.add_row(
                    str(sig.id),
                    sig.entity_id[:12] + "...",
                    sig.signal_type,
                    f"[{conf_color}]{sig.confidence:.0%}[/{conf_color}]",
                    (sig.description or "")[:40],
                    sig.detected_at.strftime("%Y-%m-%d %H:%M"),
                    processed_str,
                )

            console.print(table)
            rprint(f"\nTotal: [bold]{len(signals)}[/bold] signals")

    asyncio.run(_list_signals())


@signals_app.command("stats")
def signals_stats(
    entity_id: Annotated[
        str | None,
        typer.Option("--entity", "-e", help="Filter by entity ID"),
    ] = None,
    days: Annotated[
        int,
        typer.Option("--days", "-d", help="Statistics for last N days"),
    ] = 30,
) -> None:
    """Show signal statistics.

    Example:
        sentinel signals stats --days 7
    """
    from src.sentinel.signal_service import SignalService

    async def _stats() -> None:
        async with get_session() as session:
            service = SignalService(session)

            stats = await service.get_signal_stats(entity_id=entity_id, days=days)

            rprint(f"\n[bold]Signal Statistics ({stats['period_days']} days)[/bold]")

            if entity_id:
                rprint(f"Entity: [cyan]{entity_id}[/cyan]")

            rprint(f"\n  Total signals: [bold]{stats['total_signals']}[/bold]")
            rprint(f"  Processed: [green]{stats['processed']}[/green]")
            rprint(f"  Unprocessed: [yellow]{stats['unprocessed']}[/yellow]")
            rprint(f"  High confidence: [red]{stats['high_confidence']}[/red]")
            rprint(f"  Avg confidence: {stats['avg_confidence']:.0%}")

            if stats.get("by_type"):
                rprint("\n[bold]By Type:[/bold]")
                for sig_type, count in sorted(stats["by_type"].items(), key=lambda x: x[1], reverse=True):
                    rprint(f"  {sig_type}: {count}")

            if stats.get("by_entity"):
                rprint("\n[bold]By Entity:[/bold]")
                for ent_id, count in sorted(stats["by_entity"].items(), key=lambda x: x[1], reverse=True)[:10]:
                    rprint(f"  {ent_id}: {count}")

    asyncio.run(_stats())


@signals_app.command("analyze")
def signals_analyze(
    entity_id: Annotated[
        str,
        typer.Argument(..., help="Entity ID to analyze"),
    ],
    days: Annotated[
        int,
        typer.Option("--days", "-d", help="Analyze last N days"),
    ] = 7,
) -> None:
    """Run temporal analysis on an entity.

    Example:
        sentinel signals analyze ent_abc123 --days 14
    """
    from src.monitor.temporal_analyzer import TemporalAnalyzer

    async def _analyze() -> None:
        async with get_session() as session:
            analyzer = TemporalAnalyzer(session)

            rprint(f"[bold blue]Analyzing {entity_id} for temporal anomalies...[/bold blue]")

            signals = await analyzer.analyze_and_create_signals(entity_id, lookback_days=days)

            if not signals:
                rprint("[green]No anomalies detected[/green]")
                return

            rprint(f"\n[bold yellow]Detected {len(signals)} anomalies:[/bold yellow]")

            for signal in signals:
                conf_color = "red" if signal.confidence >= 0.7 else "yellow"
                rprint(f"\n  [{conf_color}]{signal.signal_type}[/{conf_color}] ({signal.confidence:.0%})")
                if signal.description:
                    rprint(f"    {signal.description}")

            await session.commit()

    asyncio.run(_analyze())


if __name__ == "__main__":
    app()
