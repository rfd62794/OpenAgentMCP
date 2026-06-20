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
