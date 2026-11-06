"""Ruff lint + format check over the repo's Python files (runs in-suite)."""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    str(REPO_ROOT / "components"),
    str(REPO_ROOT / "tests"),
]


def ruff_cmd():
    exe = shutil.which("ruff")
    if exe:
        return [exe]
    return [sys.executable, "-m", "ruff"]


def run_ruff(*args):
    return subprocess.run(
        [*ruff_cmd(), *args, *TARGETS],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_ruff_check():
    proc = run_ruff("check")
    assert proc.returncode == 0, f"ruff check failed:\n{proc.stdout}\n{proc.stderr}"


def test_ruff_format():
    proc = run_ruff("format", "--check")
    assert proc.returncode == 0, (
        f"ruff format --check failed (run `ruff format`):\n{proc.stdout}\n{proc.stderr}"
    )
