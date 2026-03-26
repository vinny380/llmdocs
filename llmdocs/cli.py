"""
Command-line interface for llmdocs.

End users invoke `llmdocs` after `pip install llmdocs`. Server and indexing
logic live in other modules and are loaded by these commands (and by the
Docker image entrypoint), not as a supported public Python API.
"""

from __future__ import annotations

import click

from llmdocs import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="llmdocs")
def cli() -> None:
    """Agent-first documentation platform — CLI only; not a Python SDK."""


@cli.command("init")
def init() -> None:
    """Scaffold llmdocs config and docker-compose in the current project."""
    raise click.ClickException("Not implemented yet — coming in a later task.")


@cli.command("serve")
@click.option(
    "--watch/--no-watch",
    default=False,
    help="Watch docs and reload (when implemented).",
)
def serve(watch: bool) -> None:
    """Start the documentation server."""
    del watch
    raise click.ClickException("Not implemented yet — coming in a later task.")


@cli.command("build")
def build() -> None:
    """Pre-build the search index."""
    raise click.ClickException("Not implemented yet — coming in a later task.")


@cli.command("validate")
def validate() -> None:
    """Validate documentation health."""
    raise click.ClickException("Not implemented yet — coming in a later task.")


@cli.command("version")
def version_cmd() -> None:
    """Print the package version."""
    click.echo(__version__)
