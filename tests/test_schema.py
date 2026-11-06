"""Unit tests for the sx126x_radiolib CONFIG_SCHEMA (no toolchain needed)."""

import esphome.config_validation as cv
import pytest


def minimal_config(**overrides):
    cfg = {
        "cs_pin": 5,
        "sck_pin": 7,
        "mosi_pin": 9,
        "miso_pin": 8,
        "dio1_pin": 2,
        "busy_pin": 4,
        "rst_pin": 3,
        "rf_switch": True,
        "frequency": "868MHz",
        "hw_version": "sx1262",
        "modulation": "LORA",
    }
    cfg.update(overrides)
    return cfg


def test_minimal_valid(comp):
    validated = comp.CONFIG_SCHEMA(minimal_config())
    assert validated["spreading_factor"] == 9
    assert validated["pa_power"] == 14
    assert validated["crc_enable"] is True
    assert validated["rx_start"] is True
    assert validated["sync_value"] == [0x12]
    assert validated["bandwidth"] == "125_0kHz"
    assert validated["bandwidth"].enum_value == 125.0
    assert validated["coding_rate"] == "CR_4_5"
    assert validated["coding_rate"].enum_value == 5
    assert validated["tcxo_voltage"] == "NONE"
    assert validated["tcxo_voltage"].enum_value == 0.0
    assert validated["pa_ramp"] == "40us"
    assert validated["pa_ramp"].enum_value == 0x03


def test_full_valid_with_rxen(comp):
    # on_packet automation is covered by the examples integration test
    # (it needs full ESPHome core context, not available standalone).
    cfg = minimal_config(
        rxen_pin=6,
        txen_pin=48,
        bandwidth="500_0kHz",
        spreading_factor=12,
        coding_rate="CR_4_8",
        sync_value=[0x14, 0x24],
        preamble_size=12,
        crc_enable=True,
        pa_power=22,
        pa_ramp="1700us",
        tcxo_voltage="1_8V",
        tcxo_delay="10ms",
        rx_start=True,
    )
    validated = comp.CONFIG_SCHEMA(cfg)
    assert validated["rxen_pin"]["number"] == 6
    assert validated["spreading_factor"] == 12
    assert validated["bandwidth"].enum_value == 500.0
    assert validated["tcxo_voltage"].enum_value == 1.8


def test_fsk_rejected_without_fsk_bandwidth(comp):
    # FSK is valid, but the LoRa-default bandwidth is not usable with it.
    with pytest.raises(cv.Invalid, match="LoRa bandwidth"):
        comp.CONFIG_SCHEMA(minimal_config(modulation="FSK"))


def test_sf6_rejected(comp):
    with pytest.raises(cv.Invalid, match="Spreading factor 6"):
        comp.CONFIG_SCHEMA(minimal_config(spreading_factor=6))


def test_preamble_too_short_rejected(comp):
    with pytest.raises(cv.Invalid, match="Minimum 'preamble_size'"):
        comp.CONFIG_SCHEMA(minimal_config(preamble_size=4))


def test_sync_value_too_long_rejected(comp):
    with pytest.raises(cv.Invalid, match="at most 2 bytes"):
        comp.CONFIG_SCHEMA(minimal_config(sync_value=[0x11, 0x22, 0x33]))


def test_missing_required_pin_rejected(comp):
    cfg = minimal_config()
    del cfg["busy_pin"]
    with pytest.raises(cv.Invalid):
        comp.CONFIG_SCHEMA(cfg)


def test_validate_raw_data(comp):
    assert comp.validate_raw_data("hi") == b"hi"
    assert comp.validate_raw_data([0x01, 0xFF]) == [0x01, 0xFF]
    with pytest.raises(cv.Invalid, match="string wrapped in quotes"):
        comp.validate_raw_data(12345)


def fsk_config(**overrides):
    cfg = minimal_config(
        modulation="FSK",
        bandwidth="78_2kHz",
        sync_value=[0x33, 0x33],
    )
    cfg.update(overrides)
    return cfg


def test_fsk_minimal_valid(comp):
    validated = comp.CONFIG_SCHEMA(fsk_config())
    assert validated["bandwidth"] == "78_2kHz"
    assert validated["bandwidth"].enum_value == 78.2
    assert validated["bitrate"] == 4800
    assert validated["shaping"] == "NONE"


def test_fsk_rejects_lora_bandwidth(comp):
    with pytest.raises(cv.Invalid, match="LoRa bandwidth"):
        comp.CONFIG_SCHEMA(fsk_config(bandwidth="125_0kHz"))


def test_lora_rejects_fsk_bandwidth(comp):
    with pytest.raises(cv.Invalid, match="FSK bandwidth"):
        comp.CONFIG_SCHEMA(minimal_config(bandwidth="78_2kHz"))


def test_lora_rejects_fsk_only_option(comp):
    with pytest.raises(cv.Invalid, match="'bitrate' is FSK-only"):
        comp.CONFIG_SCHEMA(minimal_config(bitrate=9600))


def test_lora_rejects_payload_length(comp):
    with pytest.raises(cv.Invalid, match="'payload_length' is FSK-only"):
        comp.CONFIG_SCHEMA(minimal_config(payload_length=8))


def test_fsk_rejects_long_sync(comp):
    with pytest.raises(cv.Invalid, match="at most 8 bytes"):
        comp.CONFIG_SCHEMA(fsk_config(sync_value=[0x11] * 9))


def test_fsk_rejects_spreading_factor(comp):
    with pytest.raises(cv.Invalid, match="'spreading_factor' is LoRa-only"):
        comp.CONFIG_SCHEMA(fsk_config(spreading_factor=7))
