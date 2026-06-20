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
