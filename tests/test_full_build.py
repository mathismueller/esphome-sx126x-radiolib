"""Slow end-to-end build: full firmware compile of one example.

Opt-in only (`uv run pytest -m slow`); needs PlatformIO toolchains + network.
Mirrors upstream's test_build_components.py idea on a single board target.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

REPO_ROOT = Path(__file__).resolve().parent.parent


def esphome_cmd():
    exe = shutil.which("esphome")
    if exe:
        return [exe]
    return [sys.executable, "-m", "esphome"]


def test_full_compile_xiao_s3_wio_v10(tmp_path):
    example = REPO_ROOT / "examples" / "xiao_s3_wio_v10.yaml"
    proc = subprocess.run(
        [*esphome_cmd(), "compile", str(example)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=1500,
    )
    assert proc.returncode == 0, (
        f"full compile failed:\n{proc.stdout[-4000:]}\n{proc.stderr[-4000:]}"
    )
    built = list((REPO_ROOT / "examples" / ".esphome").rglob("firmware.elf"))
    assert built, "compile succeeded but no firmware.elf found"
