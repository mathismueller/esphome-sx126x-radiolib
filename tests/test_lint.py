"""Style checks mirroring upstream ESPHome tooling: ruff, yamllint, clang-format."""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PY_TARGETS = [str(REPO_ROOT / "components"), str(REPO_ROOT / "tests")]
YAML_TARGETS = [str(p) for p in sorted((REPO_ROOT / "examples").glob("*.yaml"))]
CPP_TARGETS = [
    str(p) for p in sorted((REPO_ROOT / "components").rglob("*")) if p.suffix in {".cpp", ".h"}
]


def run_cmd(cmd, *args):
    exe = shutil.which(cmd)
    full = [exe] if exe else [sys.executable, "-m", cmd]
    return subprocess.run(
        [*full, *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=120
    )


def test_ruff_check():
    proc = run_cmd("ruff", "check", *PY_TARGETS)
    assert proc.returncode == 0, f"ruff check failed:\n{proc.stdout}\n{proc.stderr}"


def test_ruff_format():
    proc = run_cmd("ruff", "format", "--check", *PY_TARGETS)
    assert proc.returncode == 0, (
        f"ruff format --check failed (run `ruff format`):\n{proc.stdout}\n{proc.stderr}"
    )


def test_yamllint_examples():
    proc = run_cmd("yamllint", "-c", str(REPO_ROOT / ".yamllint"), *YAML_TARGETS)
    assert proc.returncode == 0, f"yamllint failed:\n{proc.stdout}\n{proc.stderr}"


def test_clang_format():
    proc = run_cmd("clang-format", "--dry-run", "--Werror", *CPP_TARGETS)
    assert proc.returncode == 0, (
        f"clang-format found diffs (run `clang-format -i ...`):\n{proc.stdout}\n{proc.stderr}"
    )
