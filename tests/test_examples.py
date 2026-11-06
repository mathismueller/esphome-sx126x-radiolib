"""Validate every example YAML with the real `esphome config` validator."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPONENTS_DIR = REPO_ROOT / "components"


def esphome_cmd():
    exe = shutil.which("esphome")
    if exe:
        return [exe]
    return [sys.executable, "-m", "esphome"]


def run_esphome(args, cwd):
    return subprocess.run(
        [*esphome_cmd(), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=300,
    )


def stage_example(example, tmp_path):
    """Copy the example next to an absolute external_components path."""
    text = example.read_text()
    assert "../components" in text, "example must reference ../components"
    staged = tmp_path / example.name
    staged.write_text(text.replace("../components", str(COMPONENTS_DIR)))
    return staged


@pytest.mark.parametrize(
    "example", sorted(Path(__file__).parent.parent.joinpath("examples").glob("*.yaml"))
)
def test_example_validates(example, tmp_path):
    assert example.stat().st_size > 0
    staged = stage_example(example, tmp_path)
    proc = run_esphome(["config", str(staged)], cwd=tmp_path)
    assert proc.returncode == 0, (
        f"esphome config failed for {example.name}:\n"
        f"--- stdout ---\n{proc.stdout[-4000:]}\n"
        f"--- stderr ---\n{proc.stderr[-4000:]}"
    )
    assert "sx126x_radiolib:" in proc.stdout


@pytest.mark.parametrize(
    "example", sorted(Path(__file__).parent.parent.joinpath("examples").glob("*.yaml"))
)
def test_example_codegen(example, tmp_path):
    """Run full codegen (to_code) without needing toolchains."""
    staged = stage_example(example, tmp_path)
    proc = run_esphome(["compile", "--only-generate", str(staged)], cwd=tmp_path)
    assert proc.returncode == 0, (
        f"esphome codegen failed for {example.name}:\n"
        f"--- stdout ---\n{proc.stdout[-4000:]}\n"
        f"--- stderr ---\n{proc.stderr[-4000:]}"
    )
    generated = [
        p
        for p in tmp_path.rglob("main.cpp")
        if "build" in p.parts and p.parent.name == "src"
    ]
    assert generated, "codegen produced no main.cpp"
    src = generated[0].read_text()
    assert "sx126x_radiolib" in src
    assert "RadioLib" in src
