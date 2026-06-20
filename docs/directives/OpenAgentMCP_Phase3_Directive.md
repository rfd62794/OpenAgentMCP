# OpenAgentMCP — Phase 3 Directive: Writer + ScopeGuard + StateWriter + CLI

*June 2026 | Read fully before executing anything.*

---

> ⛔ **STOP:** Run pytest before touching any file.
> Must report **33 passing, 0 failing, 0 skipped**.
> If count differs, stop and report — do not proceed.

---

## §0 Context

**What exists:**
- Phase 2 certified at 33/0/0
- `Scanner`, `Assessor`, `ModelRouter`, `AssessmentResult` all live and tested
- `writer.py`, `scope_guard.py`, `state_writer.py` are stubs raising `NotImplementedError`
- `cli.py` has empty `@click.group()` — no commands yet
- Reference implementations in `C:\Github\OpenAgent\openagent\legacy\` — read for understanding, do not copy wholesale

**What Phase 3 delivers:**
1. `openagent/writer.py` — `Writer` — calls capable model, returns directive string
2. `openagent/scope_guard.py` — `ScopeGuard` — floor check + intent validation, pure logic
3. `openagent/state_writer.py` — `StateWriter` — writes `docs/state/current.md` atomically
4. `openagent/cli.py` — `analyze` command wiring all components together
5. Tests for all four with network and filesystem mocked

**What is NOT in scope:**
- MCP server — Phase 4
- `openagent init` SOUL.md interview — already in Phase 1 stub, wire in Phase 4
- `openagent serve` command — Phase 4
- habit inference, evolution loops, or any ADK-era concept — never

---

## §1 Scope Statement

| File | Status | Action |
|---|---|---|
| `openagent/writer.py` | Modify | Replace stub with implementation |
| `openagent/scope_guard.py` | Modify | Replace stub with implementation |
| `openagent/state_writer.py` | Modify | Replace stub with implementation |
| `openagent/cli.py` | Modify | Add `analyze` command |
| `tests/test_writer.py` | New | Writer tests — capable model mocked |
| `tests/test_scope_guard.py` | New | ScopeGuard tests — pure logic, no mocks needed |
| `tests/test_state_writer.py` | New | StateWriter tests — filesystem via tmp dir |
| `tests/test_cli.py` | New | CLI tests — Click CliRunner, all IO mocked |

**Read-only — do not touch:**
`openagent/models.py`, `openagent/scanner.py`, `openagent/assessor.py`,
`openagent/model_router.py`, `openagent/server.py`, `openagent/__init__.py`,
`tests/test_scaffold.py`, `tests/test_scanner.py`, `tests/test_assessor.py`,
`tests/test_model_router.py`, `tests/test_models.py`, `AGENT_CONTRACT.md`, all ADRs

---

## §2 Implementation

### 2.1 `openagent/writer.py`

Calls the capable model with assessment context. Returns directive as a string.

```python
"""
Writer — calls capable model to generate a directive from AssessmentResult.
Single network boundary: _call_model().
"""
import os
import requests
from openagent.models import AssessmentResult
from openagent.model_router import ModelRouter


class Writer:
    """Generates directives from AssessmentResult using the capable model."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.router = ModelRouter()

    def write(self, assessment: AssessmentResult, intent: str | None, soul_text: str = "") -> str:
        """
        Generate a directive for the given intent.

        assessment: output of Assessor.assess()
        intent: architect's stated goal. Falls back to assessment['what_is_next'] if None.
        soul_text: contents of SOUL.md if present, empty string otherwise.

        Raises ValueError if intent cannot be determined.
        Raises requests.HTTPError on API failure.
        """
        resolved_intent = intent or assessment.get("what_is_next", "")
        if not resolved_intent:
            raise ValueError(
                "No intent provided and assessment has no what_is_next. "
                "Pass --intent to specify the goal."
            )

        prompt = self._build_prompt(assessment, resolved_intent, soul_text)
        directive = self._call_model(prompt)
        if self.verbose:
            print(f"[writer] directive length: {len(directive)} chars")
        return directive

    def _build_prompt(self, assessment: AssessmentResult, intent: str, soul_text: str) -> str:
        repo_name = assessment.get("repo_name", "")
        phase_current = assessment.get("phase_current", "")
        what_is_built = assessment.get("what_is_built", "")
        what_is_stubbed = assessment.get("what_is_stubbed", [])
        test_floor = assessment.get("test_floor", {})
        open_questions = assessment.get("open_questions", [])
        recent_decisions = assessment.get("recent_decisions", [])
        files_in_scope = assessment.get("files_in_scope", [])

        soul_section = f"\nARCHITECT PROFILE:\n{soul_text}\n" if soul_text else ""

        return f"""You are a senior software architect writing implementation directives for AI coding agents.
{soul_section}
DIRECTIVE RULES:
1. First line: STOP rule — run pytest, report count, stop if not at expected floor.
2. State what was built last phase.
3. List files explicitly in scope. All others are read-only.
4. Implementation steps: specific, no ambiguity, no implicit decisions.
5. Test anchors: at least 8 named tests, each mapping to one behaviour.
6. Completion criteria: checklist — all items true before phase is done.
7. Never skip a failing test. Never accept skipped as passing.

Produce ONLY the directive. No preamble. No explanation after.

Repository: {repo_name}
Current phase: {phase_current}
What is built: {what_is_built}
What is stubbed: {what_is_stubbed}
Test floor: {test_floor}
Open questions: {open_questions}
Recent decisions: {recent_decisions}
Files in scope: {files_in_scope}

INTENT: {intent}"""

    def _call_model(self, prompt: str) -> str:
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        model = self.router.get_model("directive")
        resp = requests.post(
            f"{self.router.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
```

> ⚠️ RULE: `global_habits` from legacy is replaced by `soul_text: str`. Callers read SOUL.md themselves and pass the text. Writer does not read files.

> ⚠️ RULE: `_call_model` is the only network boundary. All tests mock this method.

---

### 2.2 `openagent/scope_guard.py`

Pure logic. No model calls. No IO. No external dependencies.

```python
"""
ScopeGuard — validates test floor and directive scope.
Pure logic. No model calls. No IO.
"""
import re
from typing import Any


class ScopeGuard:
    """Validates floor and directive scope. All methods are pure functions."""

    def check_floor(
        self,
        assessment: dict[str, Any],
        override: bool = False,
        override_reason: str = "",
    ) -> tuple[bool, str]:
        """
        Check whether the test floor is clean.

        Returns (ok, message). If override=True, returns ok=True with warning.
        """
        floor = assessment.get("test_floor", assessment)
        failing = floor.get("failing", 0)
        skipped = floor.get("skipped", 0)

        if override:
            return True, (
                f"OVERRIDE ACTIVE — floor not enforced. Reason: {override_reason}. "
                f"Current: {failing} failing, {skipped} skipped."
            )

        if failing > 0:
            return False, f"{failing} failing tests — fix before proceeding"
        if skipped > 0:
            return False, f"{skipped} skipped tests — 0 skipped is the invariant"
        if floor.get("passing", 0) > 0:
            return True, "Floor OK"
        return False, "No passing tests found"

    def intent_matches(
        self,
        directive: str,
        intent: str,
        files_in_scope: list[str],
    ) -> tuple[bool, list[str]]:
        """
        Check whether directive stays within the stated intent.

        Returns (ok, flags). flags are overreach warnings.
        NOTE-prefixed flags are informational only — they do not affect ok.
        """
        flags = []
        d = directive.lower()
        i = intent.lower()

        if "refactor" in d and "refactor" not in i:
            flags.append("Directive contains refactor language not in intent")

        phase_count = d.count("phase ")
        if phase_count > 2 and "roadmap" not in i:
            flags.append(f"Directive mentions {phase_count} phases — possible scope expansion")

        if not files_in_scope:
            flags.append("NOTE: files_in_scope empty — file-scope validation skipped")
        else:
            mentioned = re.findall(r"\b[\w/]+\.py\b", d)
            for fname in mentioned:
                basename = fname.split("/")[-1]
                in_scope = any(basename in f for f in files_in_scope)
                marked_new = "[new]" in d and basename in d
                if not in_scope and not marked_new:
                    flags.append(f"File out of scope and not marked [NEW]: {fname}")

        real_flags = [f for f in flags if not f.startswith("NOTE:")]
        return len(real_flags) == 0, flags

    def build_overreach_report(self, flags: list[str]) -> str:
        lines = ["=== Scope Overreach Detected ==="]
        for i, flag in enumerate(flags, 1):
            lines.append(f"{i}. {flag}")
        return "\n".join(lines)
```

> ⚠️ RULE: `ScopeGuard` has zero imports from openagent modules. It is a standalone utility. Keep it that way.

> ⚠️ RULE: Do not add model calls or IO to ScopeGuard. It must remain testable without any mocking.

---

### 2.3 `openagent/state_writer.py`

Pure stdlib. Writes `docs/state/current.md` atomically.

```python
"""
StateWriter — writes docs/state/current.md atomically.
Pure stdlib. No external dependencies.
"""
import datetime
import os
from pathlib import Path
from openagent.models import AssessmentResult


class StateWriter:
    """Writes project state to docs/state/current.md."""

    AGENT_NAME = "OpenAgentMCP v0.3"

    def write(
        self,
        repo_path: Path | str,
        assessment: AssessmentResult,
        intent: str | None,
        directive: str,
    ) -> Path:
        """
        Write current.md to docs/state/ under repo_path.
        Uses atomic tmp-then-replace to avoid partial writes.
        Returns the path of the written file.
        """
        repo_path = Path(repo_path)
        state_dir = repo_path / "docs" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        content = self._build_content(assessment, intent, directive)

        final_path = state_dir / "current.md"
        tmp_path = state_dir / "current.tmp"

        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, final_path)
        return final_path

    def _build_content(
        self,
        assessment: AssessmentResult,
        intent: str | None,
        directive: str,
    ) -> str:
        now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        phase = assessment.get("phase_current", "")
        test_passing = assessment.get("test_floor", {}).get("passing", 0)
        what_is_built = assessment.get("what_is_built", "")
        what_is_next = intent or assessment.get("what_is_next", "")

        open_questions = assessment.get("open_questions", [])
        recent_decisions = assessment.get("recent_decisions", [])

        oq_lines = "\n".join(f"- {q}" for q in open_questions) if open_questions else "- None"
        rd_lines = "\n".join(f"- {d}" for d in recent_decisions) if recent_decisions else "- None"

        return (
            f"updated: {now_date}\n"
            f"agent: {self.AGENT_NAME}\n"
            f"phase: {phase}\n"
            f"test_floor: {test_passing} passing, 0 failing, 0 skipped\n"
            f"what_is_built: {what_is_built}\n"
            f"what_is_next: {what_is_next}\n"
            f"\nopen_questions:\n{oq_lines}\n"
            f"\nrecent_decisions:\n{rd_lines}\n"
            f"\ndirective_generated: {now_time}\n"
        )
```

> ⚠️ RULE: `write()` always uses atomic replace. Never write directly to `current.md`.

> ⚠️ RULE: Agent name is `AGENT_NAME = "OpenAgentMCP v0.3"` — not the legacy "OpenAgent v0.1".

---

### 2.4 `openagent/cli.py` — `analyze` command

Add the `analyze` command. Wire all components in sequence:
`Scanner → read SOUL.md → Assessor → ScopeGuard.check_floor → Writer → ScopeGuard.intent_matches → StateWriter`

```python
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
```

> ⚠️ RULE: All imports from openagent modules inside the command function body — not at module level. This keeps `cli.py` importable without triggering `requests` or other deps.

> ⚠️ RULE: Scope check flags are warnings printed to stderr — they do not exit(1). Only floor failure exits.

---

## §3 Test Anchors

### `tests/test_writer.py` — mock `Writer._call_model`

| Test | Behaviour |
|---|---|
| `test_write_returns_directive_string` | Mock `_call_model` → returns non-empty string |
| `test_write_uses_intent_param` | Intent passed → appears in prompt sent to model |
| `test_write_falls_back_to_what_is_next` | intent=None, assessment has what_is_next → used |
| `test_write_raises_if_no_intent` | intent=None, no what_is_next → raises ValueError |
| `test_write_includes_soul_text_in_prompt` | soul_text provided → appears in prompt |
| `test_call_model_not_invoked_directly` | All tests use mock — no real API call |
| `test_write_strips_whitespace` | Model returns padded output → directive is stripped |

### `tests/test_scope_guard.py` — no mocks needed

| Test | Behaviour |
|---|---|
| `test_floor_ok_when_clean` | passing=5, failing=0, skipped=0 → ok=True |
| `test_floor_fails_on_failing` | failing=1 → ok=False, message mentions failing |
| `test_floor_fails_on_skipped` | skipped=1 → ok=False, message mentions skipped |
| `test_floor_override_returns_true` | override=True → ok=True regardless of failing |
| `test_floor_override_message_warns` | override=True → message contains "OVERRIDE" |
| `test_intent_matches_clean` | Directive mentions only scoped files → ok=True, no flags |
| `test_intent_flags_out_of_scope_file` | Directive mentions unscoped.py → flag added |
| `test_intent_flags_refactor_language` | "refactor" in directive, not in intent → flagged |
| `test_intent_empty_scope_adds_note` | files_in_scope=[] → NOTE flag, ok still True |
| `test_overreach_report_format` | flags list → report starts with "=== Scope Overreach" |

### `tests/test_state_writer.py` — tmp dir fixture

| Test | Behaviour |
|---|---|
| `test_write_creates_current_md` | Writes to `docs/state/current.md` in tmp repo |
| `test_write_returns_path` | Returns Path pointing to current.md |
| `test_write_atomic` | tmp file cleaned up after write |
| `test_content_includes_phase` | assessment phase_current appears in file |
| `test_content_includes_agent_name` | "OpenAgentMCP v0.3" in written content |
| `test_content_includes_intent` | intent string appears in what_is_next field |

### `tests/test_cli.py` — Click CliRunner + mocks

| Test | Behaviour |
|---|---|
| `test_analyze_exits_0_on_success` | Mock Scanner, Assessor, Writer, StateWriter → exit code 0 |
| `test_analyze_prints_directive` | Directive string appears in CLI output |
| `test_analyze_exits_1_on_floor_failure` | Floor failing=1 → exit code 1 |
| `test_analyze_accepts_path_arg` | Path argument passed through to Scanner |

**Target: 57 passing, 0 failing, 0 skipped** (33 existing + 24 new)

---

## §4 Completion Criteria

- [ ] pytest: **57 passing, 0 failing, 0 skipped** — raw terminal output pasted
- [ ] `openagent analyze --help` shows path arg and --intent option
- [ ] `openagent analyze . --intent "add tests for scanner"` runs end-to-end with real `OPENROUTER_API_KEY` and prints a directive (manual verification — screenshot or paste output)
- [ ] `docs/state/current.md` updated in the target repo after successful run
- [ ] No test makes a real network request — verified by running without `OPENROUTER_API_KEY` set
- [ ] `openagent/writer.py`, `openagent/scope_guard.py`, `openagent/state_writer.py` no longer raise `NotImplementedError`
- [ ] `docs/state/current.md` in OpenAgentMCP repo updated: phase 3, floor 57/0/0, next = Phase 4 (MCP server + serve command)

---

## §5 Quick Reference

| Key | Value |
|---|---|
| Baseline floor | 33/0/0 |
| Target floor | 57/0/0 |
| Writer network mock | `openagent.writer.Writer._call_model` |
| StateWriter agent name | `OpenAgentMCP v0.3` |
| Scope flags | Warnings only — do not exit(1) |
| Floor failure | Exits with code 1 |
| SOUL.md | Read by CLI, passed as `soul_text` string to Writer |
| current.md reader | `_read_current_md()` in cli.py — simple key: val parser |
| Legacy reference | `C:\Github\OpenAgent\openagent\legacy\` — read only |
| Phase 4 | MCP server + `openagent serve` command |
