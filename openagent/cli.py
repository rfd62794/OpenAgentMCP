"""CLI entry point — openagent command."""
import click


@click.group()
@click.version_option("0.3.0")
def cli():
    """OpenAgent v0.3 — repo-aware directive generator."""


# Commands added in Phase 2 (analyze, init) and Phase 4 (serve)
