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
        test_floor = current_md.get("test_floor", "unknown")
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
Test floor: {test_floor}
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
