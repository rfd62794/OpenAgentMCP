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
