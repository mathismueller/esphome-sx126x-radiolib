import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPONENT_DIR = REPO_ROOT / "components" / "sx126x_radiolib"
EXAMPLES_DIR = REPO_ROOT / "examples"


def _init_core_for_esp32():
    # Pin schemas resolve through CORE (target platform) plus the platform's
    # registered pin validator, both only populated during a real
    # `esphome config/compile` run. Fake both for unit tests.
    from esphome.components.esp32.const import KEY_BOARD, VARIANT_ESP32S3
    from esphome.const import KEY_CORE, KEY_ESP32, KEY_TARGET_PLATFORM, KEY_VARIANT
    from esphome.core import CORE

    CORE.data.setdefault(KEY_CORE, {})[KEY_TARGET_PLATFORM] = "esp32"
    CORE.data.setdefault(KEY_ESP32, {})[KEY_BOARD] = "esp32-s3-devkitc-1"
    CORE.data[KEY_ESP32][KEY_VARIANT] = VARIANT_ESP32S3
    import esphome.components.esp32.gpio  # noqa: F401 (registers pin schema)


def _load_component():
    _init_core_for_esp32()
    path = COMPONENT_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location("_sx126x_radiolib_comp", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_sx126x_radiolib_comp"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def comp():
    return _load_component()


@pytest.fixture(autouse=True)
def _config_path_context():
    # Pin registration records the config path of each pin use; provide one.
    from esphome.config import path_context

    token = path_context.set(["sx126x_radiolib"])
    yield
    path_context.reset(token)


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def examples_dir():
    return EXAMPLES_DIR
