"""Unit tests for the packet_transport platform schema."""

import importlib.util
import sys

import esphome.config_validation as cv
import pytest


def load_platform(comp):
    from pathlib import Path

    # The platform module does `from .. import ...`, so it must be imported
    # as a submodule of a package whose attribute is the parent component.
    comp.__path__ = [str(Path(comp.__file__).parent)]
    sys.modules["sxpt_pkg"] = comp
    path = Path(comp.__file__).parent / "packet_transport" / "__init__.py"
    spec = importlib.util.spec_from_file_location("sxpt_pkg.packet_transport", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sxpt_pkg.packet_transport"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_platform_minimal_valid(comp):
    pt = load_platform(comp)
    validated = pt.CONFIG_SCHEMA({"sx126x_radiolib_id": "radio"})
    assert validated["sx126x_radiolib_id"].id == "radio"


def test_platform_rejects_unknown_parent(comp):
    pt = load_platform(comp)
    with pytest.raises(cv.Invalid):
        pt.CONFIG_SCHEMA({"sx126x_radiolib_id": 123})
