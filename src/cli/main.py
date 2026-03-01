"""CLI main entry point for Sentinel commands."""

import asyncio
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


if __name__ == "__main__":
    app()
