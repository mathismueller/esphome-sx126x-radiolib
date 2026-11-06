# esphome-sx126x-radiolib

ESPHome external component: drive Semtech SX1261/1262/1268/LLCC68 radios through
[RadioLib](https://github.com/jgromes/RadioLib), with the same YAML surface as the
core `sx126x` component — plus MCU-driven antenna switch pins.

## Why this exists

The core `sx126x` component only supports a switch driven by the radio's DIO2 pin
(`rf_switch: true/false`). Boards like the Seeed **Wio-SX1262 V1.0 header version**
route the antenna switch to a separate MCU pin (`RF_SW`, e.g. XIAO `D5/GPIO6`),
which the core component cannot drive — RX stays deaf (or TX broken). This
component keeps the core YAML (`send_packet`, `on_packet`, same LoRa params) and
adds `rxen_pin` / `txen_pin`, driven automatically by RadioLib on every
TX/RX/standby transition.

Verified on: XIAO ESP32S3 + Wio-SX1262 V1.0, 868 MHz, BW125, SF9, TCXO 1.8 V —
clean bidirectional PingPong at RSSI -22 dBm before this was written.

## Requirements

- ESPHome 2026.10.2 (validation + codegen target)
- `esp32` with `framework: type: arduino` (RadioLib uses its Arduino HAL;
  the component enables Arduino's SPI library itself via
  `cg.add_library("SPI", None)`, required because ESPHome builds ESP32 targets
  through ESP-IDF with selective Arduino compilation)
- Python >= 3.12 for the tooling/tests in this repo

## Use

```yaml
external_components:
  - source:
      type: local
      path: ../components   # or wherever you clone this repo
    components: [sx126x_radiolib]

sx126x_radiolib:
  cs_pin: GPIO5
  sck_pin: GPIO7
  mosi_pin: GPIO9
  miso_pin: GPIO8
  dio1_pin: GPIO2
  busy_pin: GPIO4
  rst_pin: GPIO3
  rxen_pin: GPIO6      # <-- the part the core component cannot do
  rf_switch: true      # DIO2 drives the module-internal switch
  hw_version: sx1262
  modulation: LORA
  frequency: 868.0MHz
  tcxo_voltage: 1_8V
  on_packet:
    then:
      - lambda: |-
          ESP_LOGI("lora", "rx len=%d rssi=%.1f snr=%.1f", x.size(), rssi, snr);
```

Full example: `examples/xiao_s3_wio_v10.yaml` (XIAO ESP32S3 + Wio-SX1262 V1.0).

Same actions/triggers as core, namespaced `sx126x_radiolib.*`:
`send_packet` (`data:` string or byte list, templatable), `set_mode_rx`,
`set_mode_tx`, `set_mode_standby`, `set_mode_sleep`, `on_packet` (`x`, `rssi`, `snr`).

## Scope / roadmap

- LoRa (`modulation: LORA`, SF 7–12) and FSK (`modulation: FSK`) are
  supported. Anything else (GFSK/MSK/GMSK labels, SF6 implicit-header mode)
  fails validation with a clear error.
- `packet_transport` platform: shipped
  (`packet_transport/sx126x_radiolib`, mirrors the core platform).
  Validated live with LoRa; FSK transport is untested.
- No `run_image_cal` action (RadioLib handles image calibration during `begin()`).
- No `preamble_detect` knob (RadioLib derives the FSK preamble detector
  length automatically in `beginFSK`).

## Develop / test (uv)

```sh
uv sync --group dev        # ESPHome 2026.10.2 + pytest + ruff
uv run pytest              # schema unit tests + example validation/codegen via `esphome`
```

`tests/test_examples.py` shells out to `esphome config` on every file in
`examples/` — the same validator the dashboard/CLI runs, no toolchain needed.
A full firmware compile (`esphome compile`) is intentionally not part of the
suite (needs PlatformIO toolchains); run it manually against real hardware.
