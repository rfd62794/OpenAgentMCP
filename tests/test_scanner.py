"""Tests for openagent.scanner."""
import tempfile
from pathlib import Path
from openagent.scanner import Scanner


def test_scan_returns_required_keys():
    """Result has repo_path, file_tree, py_files, test_files, config_files, doc_files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = Scanner()
        result = scanner.scan(tmpdir)
        assert "repo_path" in result
        assert "file_tree" in result
        assert "py_files" in result
        assert "test_files" in result
        assert "config_files" in result
        assert "doc_files" in result


def test_scan_excludes_venv():
    """.venv directory not in file_tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / ".venv"
        venv_path.mkdir()
        (venv_path / "test.txt").write_text("test")
        
        scanner = Scanner()
        result = scanner.scan(tmpdir)
        assert not any(".venv" in f for f in result["file_tree"])


def test_scan_excludes_git():
    """.git directory not in file_tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        git_path = Path(tmpdir) / ".git"
        git_path.mkdir()
        (git_path / "config").write_text("test")
        
        scanner = Scanner()
        result = scanner.scan(tmpdir)
        assert not any(".git" in f for f in result["file_tree"])


def test_scan_excludes_pycache():
    """__pycache__ not in file_tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pycache_path = Path(tmpdir) / "__pycache__"
        pycache_path.mkdir()
        (pycache_path / "test.pyc").write_text("test")
        
        scanner = Scanner()
        result = scanner.scan(tmpdir)
        assert not any("__pycache__" in f for f in result["file_tree"])


def test_scan_separates_test_files():
    """Files under tests/ appear in test_files not py_files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tests_path = Path(tmpdir) / "tests"
        tests_path.mkdir()
        (tests_path / "test_example.py").write_text("test")
        
        scanner = Scanner()
        result = scanner.scan(tmpdir)
        assert "tests/test_example.py" in result["test_files"]
        assert "tests/test_example.py" not in result["py_files"]


def test_scan_file_tree_limit():
    """file_tree never exceeds 61 entries (60 + truncation marker)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create more than 60 files
        for i in range(70):
            (Path(tmpdir) / f"file{i}.txt").write_text("test")
        
        scanner = Scanner()
        result = scanner.scan(tmpdir)
        assert len(result["file_tree"]) <= 61
        if len(result["file_tree"]) == 61:
            assert result["file_tree"][-1] == "... (truncated)"


def test_scan_forward_slashes():
    """All paths in file_tree use / not \\."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("test")
        
        scanner = Scanner()
        result = scanner.scan(tmpdir)
        for path in result["file_tree"]:
            assert "\\" not in path


def test_scan_empty_repo():
    """Scans empty temp dir without error, all lists empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = Scanner()
        result = scanner.scan(tmpdir)
        assert result["file_tree"] == []
        assert result["py_files"] == []
        assert result["test_files"] == []
        assert result["config_files"] == []
        assert result["doc_files"] == []
