"""
MCP Server — exposes OpenAgent pipeline as MCP tools.
Requires: pip install openagent-directive[mcp]

Tools:
  analyze_repo(repo_path, intent) — full pipeline, writes state
  assess_repo(repo_path)          — scan + assess only, read-only
"""

try:
    from fastmcp import FastMCP
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


def _require_mcp() -> None:
    if not _MCP_AVAILABLE:
        raise ImportError(
            "MCP server requires the [mcp] extra.\n"
            "Install with: pip install openagent-directive[mcp]"
        )


def _build_server():
    """Build and return the FastMCP server instance. Called lazily."""
    from fastmcp import FastMCP
    from pathlib import Path

    mcp = FastMCP("OpenAgentMCP")

    @mcp.tool()
    def analyze_repo(repo_path: str, intent: str = "") -> dict:
        """
        Analyze a repository and generate a directive.

        Runs the full pipeline: Scanner → Assessor → Writer → StateWriter.
        Writes docs/state/current.md in the target repo.

        Args:
            repo_path: Absolute or relative path to the repository root.
            intent: Architect's goal for this phase. Falls back to what_is_next
                    in current.md if empty.

        Returns:
            dict with keys:
                directive: str — the generated directive text
                assessment: dict — AssessmentResult from Assessor
                state_path: str — path of written current.md
                floor_ok: bool — whether test floor was clean
        """
        from openagent.scanner import Scanner
        from openagent.assessor import Assessor
        from openagent.writer import Writer
        from openagent.scope_guard import ScopeGuard
        from openagent.state_writer import StateWriter

        repo = Path(repo_path).resolve()
        soul_text = _read_soul(repo)
        doc_result = _read_current_md(repo)

        scan_result = Scanner().scan(str(repo))
        assessment = Assessor().assess(scan_result, doc_result)

        guard = ScopeGuard()
        floor_ok, _ = guard.check_floor(assessment)

        writer = Writer()
        directive = writer.write(assessment, intent or None, soul_text)

        state_path = StateWriter().write(repo, assessment, intent or None, directive)

        return {
            "directive": directive,
            "assessment": assessment,
            "state_path": str(state_path),
            "floor_ok": floor_ok,
        }

    @mcp.tool()
    def assess_repo(repo_path: str) -> dict:
        """
        Assess a repository's current state without generating a directive.

        Runs Scanner + Assessor only. Does not write any files.
        Cheaper and faster than analyze_repo — useful for status checks.

        Args:
            repo_path: Absolute or relative path to the repository root.

        Returns:
            AssessmentResult dict with repo state, test floor, open questions, etc.
        """
        from openagent.scanner import Scanner
        from openagent.assessor import Assessor

        repo = Path(repo_path).resolve()
        doc_result = _read_current_md(repo)
        scan_result = Scanner().scan(str(repo))
        return Assessor().assess(scan_result, doc_result)

    @mcp.tool()
    def run_tests(repo_path: str, test_cmd: str = "") -> dict:
        """
        Spawn the repo's test suite as a background process.
        If test_cmd is empty, resolves from AGENT_CONTRACT.md or detects
        from repo contents. Returns within one second.

        Returns:
          {"status": "started", "pid": int, "log_path": str, "cmd": str}
          {"status": "error", "reason": str, "pid": None, "cmd": str|None}
        """
        from openagent.test_command_resolver import TestCommandResolver
        from openagent.test_runner import AsyncTestRunner

        cmd = test_cmd.strip() or TestCommandResolver().resolve(repo_path)
        if not cmd:
            return {
                "status": "error",
                "reason": "No test command found. Add test_cmd: <cmd> to AGENT_CONTRACT.md.",
                "pid": None,
                "cmd": None,
            }
        return AsyncTestRunner().run(repo_path, cmd)

    @mcp.tool()
    def get_test_log(repo_path: str, tail: int = 100) -> dict:
        """
        Read the async test log and check process status.
        tail: lines to return from end of log (max 200).

        Returns:
          {"status": "running"|"complete"|"not_started",
           "output": str, "exit_code": None}
        """
        from openagent.test_log_reader import TestLogReader

        return TestLogReader().read(repo_path, tail)

    @mcp.tool()
    def list_repos(root_path: str, max_repos: int = 50) -> dict:
        """
        Discover all git repos one level under root_path.
        Returns repos sorted by most-recently-active first.
        max_repos: cap on results (default 50, max 200).

        Returns:
          {"repos": [...], "count": int, "root": str}
        """
        from openagent.repo_scanner import RepoScanner

        repos = RepoScanner().scan(root_path, max_repos)
        return {"repos": repos, "count": len(repos), "root": root_path}

    return mcp


def _read_soul(repo) -> str:
    soul = repo / "SOUL.md"
    return soul.read_text(encoding="utf-8") if soul.exists() else ""


def _read_current_md(repo) -> dict:
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


def main(transport: str = "stdio", port: int = 8008) -> None:
    """Entry point for MCP server. Requires [mcp] extra."""
    _require_mcp()
    mcp = _build_server()
    if transport == "sse":
        mcp.run(transport="sse", port=port)
    else:
        mcp.run()
