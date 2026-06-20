"""CLI entry point — openagent command."""
import sys
from pathlib import Path
from typing import Optional

import click


@click.group()
@click.version_option("0.3.0")
def cli():
    """OpenAgent v0.3 — repo-aware directive generator."""


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--intent", "-i", default=None, help="Architect's goal for this phase")
@click.option("--verbose", "-v", is_flag=True, help="Verbose model output")
def analyze(path: str, intent: Optional[str], verbose: bool):
    """
    Analyze a repository and generate a directive.

    PATH defaults to current directory.
    --intent overrides what_is_next from current.md.
    """
    from openagent.scanner import Scanner
    from openagent.assessor import Assessor
    from openagent.writer import Writer
    from openagent.scope_guard import ScopeGuard
    from openagent.state_writer import StateWriter

    repo = Path(path).resolve()

    # 1. Scan
    click.echo(f"Scanning {repo} ...")
    scanner = Scanner()
    scan_result = scanner.scan(str(repo))

    # 2. Read supporting docs
    soul_text = _read_soul(repo)
    doc_result = _read_current_md(repo)

    # 3. Assess
    click.echo("Assessing repository state ...")
    assessor = Assessor(verbose=verbose)
    assessment = assessor.assess(scan_result, doc_result)

    # 4. Floor check
    guard = ScopeGuard()
    floor_ok, floor_msg = guard.check_floor(assessment)
    if not floor_ok:
        click.echo(f"Floor check failed: {floor_msg}", err=True)
        sys.exit(1)

    # 5. Write directive
    click.echo("Generating directive ...")
    writer = Writer(verbose=verbose)
    directive = writer.write(assessment, intent, soul_text)

    # 6. Scope check (warnings only — does not block)
    scope_ok, flags = guard.intent_matches(
        directive, intent or assessment.get("what_is_next", ""), assessment.get("files_in_scope", [])
    )
    if not scope_ok:
        click.echo(guard.build_overreach_report(flags), err=True)

    # 7. Write state
    state_writer = StateWriter()
    state_path = state_writer.write(repo, assessment, intent, directive)

    click.echo(f"\nState written to {state_path}\n")
    click.echo("=" * 60)
    click.echo(directive)
    click.echo("=" * 60)


@cli.command()
def serve():
    """
    Start the MCP server for Claude Desktop.

    Requires: pip install openagent-directive[mcp]

    Add to claude_desktop_config.json:
        {
          "openagent": {
            "command": "uv",
            "args": ["run", "--with", "openagent-directive[mcp]", "openagent", "serve"]
          }
        }
    """
    from openagent.server import main
    main()


def _read_soul(repo: Path) -> str:
    soul = repo / "SOUL.md"
    return soul.read_text(encoding="utf-8") if soul.exists() else ""


def _read_current_md(repo: Path) -> dict:
    current = repo / "docs" / "state" / "current.md"
    if not current.exists():
        return {"current_md": {}}
    lines = current.read_text(encoding="utf-8").splitlines()
    fields = {}
    for line in lines:
        if ": " in line:
            key, _, val = line.partition(": ")
            fields[key.strip()] = val.strip()
    return {"current_md": fields}
