"""Tests for openagent.scope_guard."""
from openagent.scope_guard import ScopeGuard


def test_floor_ok_when_clean():
    """passing=5, failing=0, skipped=0 -> ok=True."""
    guard = ScopeGuard()
    assessment = {"test_floor": {"passing": 5, "failing": 0, "skipped": 0}}
    ok, msg = guard.check_floor(assessment)
    assert ok is True
    assert "Floor OK" in msg


def test_floor_fails_on_failing():
    """failing=1 -> ok=False, message mentions failing."""
    guard = ScopeGuard()
    assessment = {"test_floor": {"passing": 5, "failing": 1, "skipped": 0}}
    ok, msg = guard.check_floor(assessment)
    assert ok is False
    assert "failing" in msg


def test_floor_fails_on_skipped():
    """skipped=1 -> ok=False, message mentions skipped."""
    guard = ScopeGuard()
    assessment = {"test_floor": {"passing": 5, "failing": 0, "skipped": 1}}
    ok, msg = guard.check_floor(assessment)
    assert ok is False
    assert "skipped" in msg


def test_floor_override_returns_true():
    """override=True -> ok=True regardless of failing."""
    guard = ScopeGuard()
    assessment = {"test_floor": {"passing": 5, "failing": 1, "skipped": 0}}
    ok, msg = guard.check_floor(assessment, override=True, override_reason="testing")
    assert ok is True


def test_floor_override_message_warns():
    """override=True -> message contains "OVERRIDE"."""
    guard = ScopeGuard()
    assessment = {"test_floor": {"passing": 5, "failing": 1, "skipped": 0}}
    ok, msg = guard.check_floor(assessment, override=True, override_reason="testing")
    assert "OVERRIDE" in msg


def test_intent_matches_clean():
    """Directive mentions only scoped files -> ok=True, no flags."""
    guard = ScopeGuard()
    directive = "Implement scanner.py with tests"
    intent = "add scanner"
    files_in_scope = ["scanner.py"]
    ok, flags = guard.intent_matches(directive, intent, files_in_scope)
    assert ok is True
    assert len(flags) == 0


def test_intent_flags_out_of_scope_file():
    """Directive mentions unscoped.py -> flag added."""
    guard = ScopeGuard()
    directive = "Implement scanner.py and unscoped.py"
    intent = "add scanner"
    files_in_scope = ["scanner.py"]
    ok, flags = guard.intent_matches(directive, intent, files_in_scope)
    assert ok is False
    assert any("unscoped.py" in f for f in flags)


def test_intent_flags_refactor_language():
    """"refactor" in directive, not in intent -> flagged."""
    guard = ScopeGuard()
    directive = "Refactor scanner.py for better performance"
    intent = "add scanner"
    files_in_scope = ["scanner.py"]
    ok, flags = guard.intent_matches(directive, intent, files_in_scope)
    assert ok is False
    assert any("refactor" in f for f in flags)


def test_intent_empty_scope_adds_note():
    """files_in_scope=[] -> NOTE flag, ok still True."""
    guard = ScopeGuard()
    directive = "Implement scanner.py"
    intent = "add scanner"
    files_in_scope = []
    ok, flags = guard.intent_matches(directive, intent, files_in_scope)
    assert ok is True
    assert any("NOTE" in f for f in flags)


def test_overreach_report_format():
    """flags list -> report starts with "=== Scope Overreach"."""
    guard = ScopeGuard()
    flags = ["flag1", "flag2"]
    report = guard.build_overreach_report(flags)
    assert report.startswith("=== Scope Overreach")
