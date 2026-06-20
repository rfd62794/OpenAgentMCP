# OpenAgentMCP — Phase 2 Directive: Scanner + Assessor + ModelRouter

*June 2026 | Read fully before executing anything.*

---

> ⛔ **STOP:** Run pytest before touching any file.
> Must report **10 passing, 0 failing, 0 skipped**.
> If count differs, stop and report — do not proceed.

---

## §0 Context

**What exists:**
- Phase 1 scaffold certified at 10/0/0
- `scanner.py`, `assessor.py`, `model_router.py` are stubs raising `NotImplementedError`
- No external model calls, no logic anywhere
- Reference implementations exist in `C:\Github\OpenAgent\openagent\legacy\` — read for understanding, do not copy wholesale

**What Phase 2 delivers:**
1. `openagent/models.py` — `AssessmentResult` TypedDict, the contract between Scanner and Assessor
2. `openagent/model_router.py` — `ModelRouter` with env-var overrides
3. `openagent/scanner.py` — `Scanner` — file tree walking only, pure stdlib, no subprocess
4. `openagent/assessor.py` — `Assessor` — calls cheap model, returns `AssessmentResult`
5. Tests for all four with all external calls mocked

**What is NOT in scope:**
- `writer.py`, `scope_guard.py`, `state_writer.py` — Phase 3
- CLI `analyze` command — Phase 3
- MCP server — Phase 4
- `extract_ast` — deferred, not needed for core pipeline
- `collect_tests` subprocess — deferred, couples Scanner to test runner
- Any ADK, orchestration, or agent framework code — never

**Key differences from legacy:**
- `AssessmentResult` is a proper TypedDict — not a raw dict with `# type: ignore`
- `Scanner` does file walking only — no subprocess calls
- `Assessor` verbose output uses `rich` only when `verbose=True`
- `ModelRouter` models are env-var overridable
- No `from openagent.legacy` imports anywhere

---

## §1 Scope Statement

| File | Status | Action |
|---|---|---|
| `openagent/models.py` | New | `AssessmentResult` TypedDict |
| `openagent/model_router.py` | Modify | Replace stub with implementation |
| `openagent/scanner.py` | Modify | Replace stub with implementation |
| `openagent/assessor.py` | Modify | Replace stub with implementation |
| `tests/test_models.py` | New | TypedDict structure tests |
| `tests/test_model_router.py` | New | Routing tests |
| `tests/test_scanner.py` | New | Scanner tests — no filesystem side effects |
| `tests/test_assessor.py` | New | Assessor tests — OpenRouter API fully mocked |

**Read-only — do not touch:**
`openagent/writer.py`, `openagent/scope_guard.py`, `openagent/state_writer.py`,
`openagent/server.py`, `openagent/cli.py`, `openagent/__init__.py`,
`tests/test_scaffold.py`, `AGENT_CONTRACT.md`, all ADRs

---

## §2 Implementation

### 2.1 `openagent/models.py`

Define `AssessmentResult` as a TypedDict. This is the data contract between Scanner/Assessor and all downstream consumers.

```python
from typing import TypedDict

class TestFloor(TypedDict):
    passing: int
    failing: int
    skipped: int
    ok: bool

class AssessmentResult(TypedDict):
    repo_name: str
    phase_current: str
    what_is_built: str
    what_is_stubbed: list[str]
    test_floor: TestFloor
    open_questions: list[str]
    recent_decisions: list[str]
    files_in_scope: list[str]
    complexity_flags: list[str]
    doc_gaps: list[str]
```

> ⚠️ RULE: `AssessmentResult` is a TypedDict — not a Pydantic model, not a dataclass, not a plain dict. All other modules import from `openagent.models`, never from each other's internal types.

> ⚠️ RULE: Do not add fields beyond what is listed above. The Assessor prompt is built around exactly these keys. Adding fields breaks the contract.

---

### 2.2 `openagent/model_router.py`

```python
"""
ModelRouter — routes tasks to the appropriate OpenRouter model.
Two task types: 'inventory' (cheap) and 'directive' (capable).
Models are env-var overridable.
"""
import os

CHEAP_MODEL_DEFAULT = "deepseek/deepseek-chat-v3-0324"
CAPABLE_MODEL_DEFAULT = "anthropic/claude-haiku-4-5"
FALLBACK_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class ModelRouter:
    """Routes task types to OpenRouter model strings."""

    def __init__(self):
        self.base_url = OPENROUTER_BASE_URL
        self._cheap = os.getenv("OPENAGENT_CHEAP_MODEL", CHEAP_MODEL_DEFAULT)
        self._capable = os.getenv("OPENAGENT_CAPABLE_MODEL", CAPABLE_MODEL_DEFAULT)

    def get_model(self, task_type: str) -> str:
        """Return model string for task_type. Unknown types return fallback."""
        if task_type == "inventory":
            return self._cheap
        if task_type == "directive":
            return self._capable
        return FALLBACK_MODEL
```

> ⚠️ RULE: `ModelRouter` has no network calls, no side effects. It is pure configuration. Do not add any IO here.

---

### 2.3 `openagent/scanner.py`

Walks the repo file tree. Pure stdlib. No subprocess. No model calls.

```python
"""
Scanner — reads repository structure.
Returns a structured file inventory for the Assessor.
Pure stdlib. No external dependencies. No model calls.
"""
import os
from pathlib import Path

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", ".pytest_cache"}
FILE_TREE_LIMIT = 60


class Scanner:
    """Scans a repository and returns a structured file inventory."""

    def scan(self, repo_path: str) -> dict:
        """
        Scan repo_path and return structured inventory.

        Returns:
            dict with keys:
                repo_path: str
                file_tree: list[str]  — all files, relative paths, forward slashes
                py_files: list[str]   — .py files excluding tests/
                test_files: list[str] — files under tests/ ending in .py
                config_files: list[str]
                doc_files: list[str]
        """
        repo = Path(repo_path).resolve()
        all_files = self._walk(repo)

        test_files = [f for f in all_files if f.startswith("tests/") and f.endswith(".py")]
        py_files = [f for f in all_files if f.endswith(".py") and f not in test_files]
        config_files = [f for f in all_files if Path(f).name in {"pyproject.toml", ".env.example", "Cargo.toml"}]
        doc_files = [f for f in all_files if Path(f).name in {"README.md", "AGENT_CONTRACT.md", "SOUL.md"}]

        handled = set(test_files + py_files + config_files + doc_files)
        other_files = [f for f in all_files if f not in handled]

        file_tree = self._truncate(py_files, test_files, config_files, doc_files, other_files)

        return {
            "repo_path": str(repo),
            "file_tree": file_tree,
            "py_files": py_files,
            "test_files": test_files,
            "config_files": config_files,
            "doc_files": doc_files,
        }

    def _walk(self, repo: Path) -> list[str]:
        """Walk repo, skip excluded dirs, return relative paths with forward slashes."""
        result = []
        for root, dirs, files in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in sorted(files):
                rel = os.path.relpath(os.path.join(root, file), repo)
                result.append(rel.replace("\\", "/"))
        return sorted(result)

    def _truncate(self, py_files, test_files, config_files, doc_files, other_files) -> list[str]:
        """Assemble file_tree up to FILE_TREE_LIMIT, prioritising test files."""
        budget = FILE_TREE_LIMIT - len(test_files)
        py_part = py_files[:budget]
        budget -= len(py_part)
        config_part = config_files[:budget]
        budget -= len(config_part)
        doc_part = doc_files[:budget]
        budget -= len(doc_part)
        other_part = other_files[:budget]

        tree = py_part + test_files + config_part + doc_part + other_part
        if (len(py_files) + len(test_files) + len(config_files) +
                len(doc_files) + len(other_files)) > FILE_TREE_LIMIT:
            tree.append("... (truncated)")
        return tree
```

> ⚠️ RULE: `Scanner` must not call subprocess, pytest, or any external process. File walking only. If test collection is needed in future, it gets its own module.

> ⚠️ RULE: `scan()` always returns all five keys. Never omit a key even if the list is empty.

---

### 2.4 `openagent/assessor.py`

Calls the cheap model with Scanner output. Returns `AssessmentResult`.

```python
"""
Assessor — calls cheap model to assess repository state.
Takes Scanner output, returns AssessmentResult.
One external dependency: requests (OpenRouter API).
"""
import json
import os
import re
import ast as ast_module
from typing import Any

import requests

from openagent.models import AssessmentResult, TestFloor
from openagent.model_router import ModelRouter

_REQUIRED_KEYS = [
    "repo_name", "phase_current", "what_is_built", "what_is_stubbed",
    "test_floor", "open_questions", "recent_decisions",
    "files_in_scope", "complexity_flags", "doc_gaps",
]


class Assessor:
    """Assesses repository state using cheap model. Returns AssessmentResult."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.router = ModelRouter()

    def assess(self, scan_result: dict, doc_result: dict) -> AssessmentResult:
        """
        Build prompt from scan_result + doc_result, call cheap model,
        parse and return AssessmentResult.

        scan_result: output of Scanner.scan()
        doc_result:  dict with optional key 'current_md' (parsed current.md fields)
        """
        prompt = self._build_prompt(scan_result, doc_result)
        raw = self._call_model(prompt)
        if self.verbose:
            print(f"[assessor] raw model output:\n{raw}\n")
        return self._parse(raw)

    def _build_prompt(self, scan_result: dict, doc_result: dict) -> str:
        import os as _os
        repo_name = _os.path.basename((scan_result.get("repo_path") or "").rstrip("/\\"))
        file_tree = "\n".join(scan_result.get("file_tree", []))

        current_md = doc_result.get("current_md", {})
        phase = current_md.get("phase", "unknown")
        what_is_built = current_md.get("what_is_built", "")
        what_is_next = current_md.get("what_is_next", "")
        open_questions = current_md.get("open_questions", "")
        recent_decisions = current_md.get("recent_decisions", "")

        return f"""You are a senior software architect analyzing a repository.
Output ONLY valid JSON with exactly these keys:
{{
  "repo_name": "string",
  "phase_current": "string",
  "what_is_built": "string",
  "what_is_stubbed": ["list of string"],
  "test_floor": {{"passing": 0, "failing": 0, "skipped": 0, "ok": true}},
  "open_questions": ["list of string"],
  "recent_decisions": ["list of string"],
  "files_in_scope": ["list of string"],
  "complexity_flags": ["list of string"],
  "doc_gaps": ["list of string"]
}}
No other keys. No markdown. No explanation.

Repository: {repo_name}
File tree:
{file_tree}

Current state:
Phase: {phase}
What is built: {what_is_built}
What is next: {what_is_next}
Open questions: {open_questions}
Recent decisions: {recent_decisions}

Produce JSON now."""

    def _call_model(self, prompt: str) -> str:
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        model = self.router.get_model("inventory")
        resp = requests.post(
            f"{self.router.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "temperature": 0.0, "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _parse(self, raw: str) -> AssessmentResult:
        """Extract JSON from raw model output. Raises ValueError on failure."""
        # Strip markdown fences if present
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
        clean = match.group(1) if match else raw.strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            py_clean = re.sub(r"\btrue\b", "True", clean)
            py_clean = re.sub(r"\bfalse\b", "False", py_clean)
            py_clean = re.sub(r"\bnull\b", "None", py_clean)
            try:
                data = ast_module.literal_eval(py_clean)
            except Exception as exc:
                raise ValueError(f"Could not parse AssessmentResult JSON: {exc}\nRaw: {raw[:500]}") from exc

        missing = [k for k in _REQUIRED_KEYS if k not in data]
        if missing:
            raise ValueError(f"AssessmentResult missing keys: {missing}")

        tf = data["test_floor"]
        tf["ok"] = tf.get("failing", 1) == 0 and tf.get("skipped", 1) == 0

        return data  # type: ignore[return-value]
```

> ⚠️ RULE: `_call_model` must be the only method that makes network requests. Tests mock this method. No other method touches the network.

> ⚠️ RULE: `assess()` raises `ValueError` on parse failure and `requests.HTTPError` on API failure. It never returns partial data.

---

## §3 Test Anchors

All OpenRouter API calls must be mocked with `unittest.mock.patch`. No network calls in tests.

### `tests/test_models.py`

| Test | Behaviour |
|---|---|
| `test_assessment_result_structure` | TypedDict has all required keys |
| `test_test_floor_structure` | `TestFloor` has passing/failing/skipped/ok |

### `tests/test_model_router.py`

| Test | Behaviour |
|---|---|
| `test_inventory_returns_cheap_model` | `get_model("inventory")` returns deepseek model string |
| `test_directive_returns_capable_model` | `get_model("directive")` returns haiku model string |
| `test_unknown_type_returns_fallback` | `get_model("unknown")` returns fallback string |
| `test_env_var_overrides_cheap_model` | Set `OPENAGENT_CHEAP_MODEL` → returned by `get_model("inventory")` |
| `test_env_var_overrides_capable_model` | Set `OPENAGENT_CAPABLE_MODEL` → returned by `get_model("directive")` |
| `test_base_url_is_openrouter` | `router.base_url` contains "openrouter.ai" |

### `tests/test_scanner.py`

| Test | Behaviour |
|---|---|
| `test_scan_returns_required_keys` | Result has repo_path, file_tree, py_files, test_files, config_files, doc_files |
| `test_scan_excludes_venv` | `.venv` directory not in file_tree |
| `test_scan_excludes_git` | `.git` directory not in file_tree |
| `test_scan_excludes_pycache` | `__pycache__` not in file_tree |
| `test_scan_separates_test_files` | Files under `tests/` appear in test_files not py_files |
| `test_scan_file_tree_limit` | file_tree never exceeds 61 entries (60 + truncation marker) |
| `test_scan_forward_slashes` | All paths in file_tree use `/` not `\\` |
| `test_scan_empty_repo` | Scans empty temp dir without error, all lists empty |

### `tests/test_assessor.py`

| Test | Behaviour |
|---|---|
| `test_assess_returns_assessment_result` | Mock `_call_model` → valid JSON → returns dict with all required keys |
| `test_assess_parses_markdown_fenced_json` | Raw output wrapped in ```json ... ``` → parsed correctly |
| `test_assess_raises_on_missing_key` | JSON missing `repo_name` → raises `ValueError` |
| `test_assess_raises_on_invalid_json` | `_call_model` returns garbage → raises `ValueError` |
| `test_assess_sets_floor_ok_true` | failing=0, skipped=0 → `test_floor["ok"]` is True |
| `test_assess_sets_floor_ok_false` | failing=1 → `test_floor["ok"]` is False |
| `test_call_model_not_invoked_in_tests` | Confirm all tests use mock — no real network call |

**Target: 33 passing, 0 failing, 0 skipped** (10 existing + 23 new)

---

## §4 Completion Criteria

- [ ] pytest: **33 passing, 0 failing, 0 skipped** — raw terminal output pasted
- [ ] `from openagent.models import AssessmentResult` succeeds
- [ ] `from openagent.scanner import Scanner` succeeds and `Scanner().scan(".")` returns all 6 keys
- [ ] `from openagent.model_router import ModelRouter` succeeds
- [ ] `from openagent.assessor import Assessor` succeeds
- [ ] No test makes a real network request — verify by running tests without `OPENROUTER_API_KEY` set
- [ ] `openagent/__init__.py` unchanged — version still `0.3.0`
- [ ] `docs/state/current.md` updated: phase 2, floor 33/0/0, next = Phase 3 (Writer + ScopeGuard + CLI analyze command)

---

## §5 Quick Reference

| Key | Value |
|---|---|
| Baseline floor | 10/0/0 |
| Target floor | 33/0/0 |
| Cheap model default | `deepseek/deepseek-chat-v3-0324` |
| Capable model default | `anthropic/claude-haiku-4-5` |
| Env override (cheap) | `OPENAGENT_CHEAP_MODEL` |
| Env override (capable) | `OPENAGENT_CAPABLE_MODEL` |
| File tree limit | 60 files + optional truncation marker |
| Excluded dirs | `.git`, `.venv`, `__pycache__`, `node_modules`, `dist`, `.pytest_cache` |
| Network mock target | `openagent.assessor.Assessor._call_model` |
| Legacy reference | `C:\Github\OpenAgent\openagent\legacy\` — read only, do not import |
| Phase 3 | Writer + ScopeGuard + StateWriter + CLI `analyze` command |
| Phase 4 | MCP server + `serve` command |
