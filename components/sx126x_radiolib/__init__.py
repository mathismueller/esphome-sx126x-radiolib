from typing import Any

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation, pins
from esphome.components.const import CONF_CRC_ENABLE, CONF_ON_PACKET
from esphome.const import CONF_DATA, CONF_FREQUENCY, CONF_ID
from esphome.core import ID
from esphome.cpp_generator import MockObj
from esphome.types import ConfigType, TemplateArgsType

MULTI_CONF = True
CODEOWNERS = ["@mathis"]
DEPENDENCIES: list[str] = []

CONF_SX126X_RADIOLIB_ID = "sx126x_radiolib_id"
CONF_BANDWIDTH = "bandwidth"
CONF_CODING_RATE = "coding_rate"
CONF_CS_PIN = "cs_pin"
CONF_DIO1_PIN = "dio1_pin"
CONF_BUSY_PIN = "busy_pin"
CONF_RST_PIN = "rst_pin"
CONF_SCK_PIN = "sck_pin"
CONF_MOSI_PIN = "mosi_pin"
CONF_MISO_PIN = "miso_pin"
CONF_RXEN_PIN = "rxen_pin"
CONF_TXEN_PIN = "txen_pin"
CONF_HW_VERSION = "hw_version"
CONF_MODULATION = "modulation"
CONF_PA_POWER = "pa_power"
CONF_PA_RAMP = "pa_ramp"
CONF_BITRATE = "bitrate"
CONF_DEVIATION = "deviation"
CONF_SHAPING = "shaping"
CONF_CRC_SIZE = "crc_size"
CONF_CRC_INVERTED = "crc_inverted"
CONF_CRC_POLYNOMIAL = "crc_polynomial"
CONF_CRC_INITIAL = "crc_initial"
CONF_WHITENING_ENABLE = "whitening_enable"
CONF_WHITENING_INITIAL = "whitening_initial"
CONF_PREAMBLE_SIZE = "preamble_size"
CONF_SPREADING_FACTOR = "spreading_factor"
CONF_SYNC_VALUE = "sync_value"
CONF_TCXO_VOLTAGE = "tcxo_voltage"
CONF_TCXO_DELAY = "tcxo_delay"
CONF_RX_START = "rx_start"
CONF_RF_SWITCH = "rf_switch"
CONF_PAYLOAD_LENGTH = "payload_length"

sx126x_radiolib_ns = cg.esphome_ns.namespace("sx126x_radiolib")
SX126xRadioLib = sx126x_radiolib_ns.class_("SX126xRadioLib", cg.Component)

# LoRa-only bandwidths (kHz). FSK uses FSK_BW_KHZ below.
LORA_BW_KHZ = {
    "7_8kHz": 7.8,
    "10_4kHz": 10.4,
    "15_6kHz": 15.6,
    "20_8kHz": 20.8,
    "31_3kHz": 31.3,
    "41_7kHz": 41.7,
    "62_5kHz": 62.5,
    "125_0kHz": 125.0,
    "250_0kHz": 250.0,
    "500_0kHz": 500.0,
}

# FSK-only bandwidths (kHz) - the SX126x discrete Rx bandwidths.
FSK_BW_KHZ = {
    "4_8kHz": 4.8,
    "5_8kHz": 5.8,
    "7_3kHz": 7.3,
    "9_7kHz": 9.7,
    "11_7kHz": 11.7,
    "14_6kHz": 14.6,
    "19_5kHz": 19.5,
    "23_4kHz": 23.4,
    "29_3kHz": 29.3,
    "39_0kHz": 39.0,
    "46_9kHz": 46.9,
    "58_6kHz": 58.6,
    "78_2kHz": 78.2,
    "93_8kHz": 93.8,
    "117_3kHz": 117.3,
    "156_2kHz": 156.2,
    "187_2kHz": 187.2,
    "234_3kHz": 234.3,
    "312_0kHz": 312.0,
    "373_6kHz": 373.6,
    "467_0kHz": 467.0,
}

BW_KHZ = {**LORA_BW_KHZ, **FSK_BW_KHZ}

CODING_RATE = {
    "CR_4_5": 5,
    "CR_4_6": 6,
    "CR_4_7": 7,
    "CR_4_8": 8,
}

# PA ramp time register values, Semtech SX126x SetPaRampTime.
RAMP = {
    "10us": 0x00,
    "20us": 0x01,
    "40us": 0x03,
    "80us": 0x05,
    "200us": 0x07,
    "800us": 0x09,
    "1700us": 0x0A,
    "3400us": 0x0B,
}

SHAPING = {
    "GAUSSIAN_BT_0_3": 0x01,
    "GAUSSIAN_BT_0_5": 0x02,
    "GAUSSIAN_BT_0_7": 0x03,
    "GAUSSIAN_BT_1_0": 0x04,
    "NONE": 0x00,
}

TCXO_VOLTAGE = {
    "1_6V": 1.6,
    "1_7V": 1.7,
    "1_8V": 1.8,
    "2_2V": 2.2,
    "2_4V": 2.4,
    "2_7V": 2.7,
    "3_0V": 3.0,
    "3_3V": 3.3,
    "NONE": 0.0,
}

SendPacketAction = sx126x_radiolib_ns.class_(
    "SendPacketAction", automation.Action, cg.Parented.template(SX126xRadioLib)
)
SetModeTxAction = sx126x_radiolib_ns.class_(
    "SetModeTxAction", automation.Action, cg.Parented.template(SX126xRadioLib)
)
SetModeRxAction = sx126x_radiolib_ns.class_(
    "SetModeRxAction", automation.Action, cg.Parented.template(SX126xRadioLib)
)
SetModeSleepAction = sx126x_radiolib_ns.class_(
    "SetModeSleepAction", automation.Action, cg.Parented.template(SX126xRadioLib)
)
SetModeStandbyAction = sx126x_radiolib_ns.class_(
    "SetModeStandbyAction", automation.Action, cg.Parented.template(SX126xRadioLib)
)


def validate_raw_data(value: Any) -> bytes | list[int]:
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, list):
        return cv.Schema([cv.hex_uint8_t])(value)
    raise cv.Invalid("data must either be a string wrapped in quotes or a list of bytes")


def validate_config(config: ConfigType) -> ConfigType:
    is_fsk = config[CONF_MODULATION] == "FSK"
    bw = config[CONF_BANDWIDTH]
    if is_fsk:
        if bw not in FSK_BW_KHZ:
            raise cv.Invalid(f"{bw} is a LoRa bandwidth, pick one of the FSK bandwidths for FSK")
        if config[CONF_PREAMBLE_SIZE] < 1:
            raise cv.Invalid("Minimum 'preamble_size' is 1 with FSK")
        if len(config[CONF_SYNC_VALUE]) > 8:
            raise cv.Invalid("'sync_value' takes at most 8 bytes with FSK")
        if config[CONF_SPREADING_FACTOR] != 9:
            raise cv.Invalid("'spreading_factor' is LoRa-only")
        if config[CONF_CODING_RATE] != "CR_4_5":
            raise cv.Invalid("'coding_rate' is LoRa-only")
    else:
        if bw not in LORA_BW_KHZ:
            raise cv.Invalid(f"{bw} is an FSK bandwidth, pick one of the LoRa bandwidths for LORA")
        if config[CONF_PREAMBLE_SIZE] < 6:
            raise cv.Invalid("Minimum 'preamble_size' is 6 with LORA")
        if config[CONF_SPREADING_FACTOR] < 7:
            raise cv.Invalid(
                "Spreading factor 6 (implicit header mode) is not supported yet, use 7-12"
            )
        if len(config[CONF_SYNC_VALUE]) > 2:
            raise cv.Invalid("'sync_value' takes at most 2 bytes with LORA")
        if config[CONF_PAYLOAD_LENGTH] != 0:
            raise cv.Invalid("'payload_length' is FSK-only (LoRa always uses explicit header mode)")
        for key in (
            CONF_BITRATE,
            CONF_DEVIATION,
            CONF_SHAPING,
            CONF_CRC_SIZE,
            CONF_CRC_INVERTED,
            CONF_CRC_POLYNOMIAL,
            CONF_CRC_INITIAL,
            CONF_WHITENING_ENABLE,
            CONF_WHITENING_INITIAL,
        ):
            if config[key] != FSK_DEFAULTS[key]:
                raise cv.Invalid(f"'{key}' is FSK-only")
    return config


FSK_DEFAULTS = {
    CONF_BITRATE: 4800,
    CONF_DEVIATION: 5000,
    CONF_SHAPING: "NONE",
    CONF_CRC_SIZE: 2,
    CONF_CRC_INVERTED: True,
    CONF_CRC_POLYNOMIAL: 0x1021,
    CONF_CRC_INITIAL: 0x1D0F,
    CONF_WHITENING_ENABLE: False,
    CONF_WHITENING_INITIAL: 0x0100,
}


CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(SX126xRadioLib),
            cv.Required(CONF_CS_PIN): pins.gpio_output_pin_schema,
            cv.Required(CONF_SCK_PIN): pins.gpio_output_pin_schema,
            cv.Required(CONF_MOSI_PIN): pins.gpio_output_pin_schema,
            cv.Required(CONF_MISO_PIN): pins.gpio_input_pin_schema,
            cv.Required(CONF_DIO1_PIN): pins.gpio_input_pin_schema,
            cv.Required(CONF_BUSY_PIN): pins.gpio_input_pin_schema,
            cv.Required(CONF_RST_PIN): pins.gpio_output_pin_schema,
            cv.Optional(CONF_RXEN_PIN): pins.gpio_output_pin_schema,
            cv.Optional(CONF_TXEN_PIN): pins.gpio_output_pin_schema,
            # Same meaning as the core sx126x component: DIO2 drives an
            # external RF switch inside the module.
            cv.Required(CONF_RF_SWITCH): cv.boolean,
            cv.Required(CONF_FREQUENCY): cv.All(
                cv.frequency, cv.int_range(min=int(137e6), max=int(1020e6))
            ),
            cv.Required(CONF_HW_VERSION): cv.one_of(
                "sx1261", "sx1262", "sx1268", "llcc68", lower=True
            ),
            cv.Required(CONF_MODULATION): cv.one_of("LORA", "FSK", upper=True),
            cv.Optional(CONF_ON_PACKET): automation.validate_automation(single=True),
            cv.Optional(CONF_BANDWIDTH, default="125_0kHz"): cv.enum(BW_KHZ),
            cv.Optional(CONF_CODING_RATE, default="CR_4_5"): cv.enum(CODING_RATE),
            cv.Optional(CONF_CRC_ENABLE, default=True): cv.boolean,
            cv.Optional(CONF_BITRATE, default=4800): cv.int_range(min=600, max=300000),
            cv.Optional(CONF_DEVIATION, default="5kHz"): cv.All(
                cv.frequency, cv.int_range(min=0, max=100000)
            ),
            cv.Optional(CONF_SHAPING, default="NONE"): cv.enum(SHAPING),
            cv.Optional(CONF_CRC_SIZE, default=2): cv.int_range(min=1, max=2),
            cv.Optional(CONF_CRC_INVERTED, default=True): cv.boolean,
            cv.Optional(CONF_CRC_POLYNOMIAL, default=0x1021): cv.All(
                cv.hex_int, cv.Range(min=0, max=0xFFFF)
            ),
            cv.Optional(CONF_CRC_INITIAL, default=0x1D0F): cv.All(
                cv.hex_int, cv.Range(min=0, max=0xFFFF)
            ),
            cv.Optional(CONF_WHITENING_ENABLE, default=False): cv.boolean,
            cv.Optional(CONF_WHITENING_INITIAL, default=0x0100): cv.All(
                cv.hex_int, cv.Range(min=0, max=0x1FF)
            ),
            cv.Optional(CONF_PA_POWER, default=14): cv.int_range(min=-3, max=22),
            cv.Optional(CONF_PA_RAMP, default="40us"): cv.enum(RAMP),
            cv.Optional(CONF_PAYLOAD_LENGTH, default=0): cv.int_range(min=0, max=255),
            cv.Optional(CONF_PREAMBLE_SIZE, default=8): cv.int_range(min=1, max=65535),
            cv.Optional(CONF_RX_START, default=True): cv.boolean,
            cv.Optional(CONF_SPREADING_FACTOR, default=9): cv.int_range(min=6, max=12),
            cv.Optional(CONF_SYNC_VALUE, default=[0x12]): cv.ensure_list(cv.hex_uint8_t),
            cv.Optional(CONF_TCXO_VOLTAGE, default="NONE"): cv.enum(TCXO_VOLTAGE),
            cv.Optional(CONF_TCXO_DELAY, default="5ms"): cv.positive_time_period,
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
    .add_extra(validate_config)
)


async def to_code(config: ConfigType) -> None:
    cg.add_library("jgromes/RadioLib", "7.8.1")
    # RadioLib's Arduino HAL needs Arduino's SPI library. ESPHome builds all
    # ESP32 targets through ESP-IDF with selective Arduino compilation, so the
    # SPI library (include path + sources) must be enabled explicitly.
    cg.add_library("SPI", None)
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    if CONF_ON_PACKET in config:
        await automation.build_automation(
            var.get_packet_trigger(),
            [
                (cg.std_vector.template(cg.uint8), "x"),
                (cg.float_, "rssi"),
                (cg.float_, "snr"),
            ],
            config[CONF_ON_PACKET],
        )
    # RadioLib drives the pins itself through Arduino APIs, so only the
    # raw GPIO numbers cross the codegen boundary.
    for key, setter in (
        (CONF_CS_PIN, "set_cs_pin"),
        (CONF_SCK_PIN, "set_sck_pin"),
        (CONF_MOSI_PIN, "set_mosi_pin"),
        (CONF_MISO_PIN, "set_miso_pin"),
        (CONF_DIO1_PIN, "set_dio1_pin"),
        (CONF_BUSY_PIN, "set_busy_pin"),
        (CONF_RST_PIN, "set_rst_pin"),
    ):
        cg.add(getattr(var, setter)(config[key]["number"]))
    if CONF_RXEN_PIN in config:
        cg.add(var.set_rxen_pin(config[CONF_RXEN_PIN]["number"]))
    if CONF_TXEN_PIN in config:
        cg.add(var.set_txen_pin(config[CONF_TXEN_PIN]["number"]))
    cg.add(var.set_bandwidth(config[CONF_BANDWIDTH]))
    cg.add(var.set_fsk_mode(config[CONF_MODULATION] == "FSK"))
    cg.add(var.set_coding_rate(config[CONF_CODING_RATE]))
    cg.add(var.set_crc_enable(config[CONF_CRC_ENABLE]))
    cg.add(var.set_bitrate(config[CONF_BITRATE]))
    cg.add(var.set_deviation_hz(config[CONF_DEVIATION]))
    cg.add(var.set_shaping(config[CONF_SHAPING]))
    cg.add(var.set_crc_size(config[CONF_CRC_SIZE]))
    cg.add(var.set_crc_inverted(config[CONF_CRC_INVERTED]))
    cg.add(var.set_crc_polynomial(config[CONF_CRC_POLYNOMIAL]))
    cg.add(var.set_crc_initial(config[CONF_CRC_INITIAL]))
    cg.add(var.set_whitening_enable(config[CONF_WHITENING_ENABLE]))
    cg.add(var.set_whitening_initial(config[CONF_WHITENING_INITIAL]))
    cg.add(var.set_frequency(config[CONF_FREQUENCY]))
    cg.add(var.set_hw_version(config[CONF_HW_VERSION]))
    cg.add(var.set_pa_power(config[CONF_PA_POWER]))
    cg.add(var.set_pa_ramp(config[CONF_PA_RAMP]))
    cg.add(var.set_payload_length(config[CONF_PAYLOAD_LENGTH]))
    cg.add(var.set_preamble_size(config[CONF_PREAMBLE_SIZE]))
    cg.add(var.set_rf_switch(config[CONF_RF_SWITCH]))
    cg.add(var.set_spreading_factor(config[CONF_SPREADING_FACTOR]))
    cg.add(var.set_sync_value(config[CONF_SYNC_VALUE]))
    cg.add(var.set_rx_start(config[CONF_RX_START]))
    cg.add(var.set_tcxo_voltage(config[CONF_TCXO_VOLTAGE]))
    delay = config[CONF_TCXO_DELAY]
    cg.add(var.set_tcxo_delay(int(delay.total_microseconds)))


NO_ARGS_ACTION_SCHEMA = automation.maybe_simple_id(
    {
        cv.GenerateID(): cv.use_id(SX126xRadioLib),
    }
)


@automation.register_action(
    "sx126x_radiolib.set_mode_tx",
    SetModeTxAction,
    NO_ARGS_ACTION_SCHEMA,
    synchronous=True,
)
@automation.register_action(
    "sx126x_radiolib.set_mode_rx",
    SetModeRxAction,
    NO_ARGS_ACTION_SCHEMA,
    synchronous=True,
)
@automation.register_action(
    "sx126x_radiolib.set_mode_standby",
    SetModeStandbyAction,
    NO_ARGS_ACTION_SCHEMA,
    synchronous=True,
)
async def no_args_action_to_code(
    config: ConfigType,
    action_id: ID,
    template_arg: cg.TemplateArguments,
    args: TemplateArgsType,
) -> MockObj:
    var = cg.new_Pvariable(action_id, template_arg)
    await cg.register_parented(var, config[CONF_ID])
    return var


SET_MODE_SLEEP_ACTION_SCHEMA = automation.maybe_simple_id(
    {
        cv.GenerateID(): cv.use_id(SX126xRadioLib),
    }
)


@automation.register_action(
    "sx126x_radiolib.set_mode_sleep",
    SetModeSleepAction,
    SET_MODE_SLEEP_ACTION_SCHEMA,
    synchronous=True,
)
async def set_mode_sleep_action_to_code(
    config: ConfigType,
    action_id: ID,
    template_arg: cg.TemplateArguments,
    args: TemplateArgsType,
) -> MockObj:
    var = cg.new_Pvariable(action_id, template_arg)
    await cg.register_parented(var, config[CONF_ID])
    return var


SEND_PACKET_ACTION_SCHEMA = cv.maybe_simple_value(
    {
        cv.GenerateID(): cv.use_id(SX126xRadioLib),
        cv.Required(CONF_DATA): cv.templatable(validate_raw_data),
    },
    key=CONF_DATA,
)


@automation.register_action(
    "sx126x_radiolib.send_packet",
    SendPacketAction,
    SEND_PACKET_ACTION_SCHEMA,
    synchronous=True,
)
async def send_packet_action_to_code(
    config: ConfigType,
    action_id: ID,
    template_arg: cg.TemplateArguments,
    args: TemplateArgsType,
) -> MockObj:
    var = cg.new_Pvariable(action_id, template_arg)
    await cg.register_parented(var, config[CONF_ID])
    data = config[CONF_DATA]
    if isinstance(data, bytes):
        data = list(data)
    if cg.is_template(data):
        templ = await cg.templatable(data, args, cg.std_vector.template(cg.uint8))
        cg.add(var.set_data_template(templ))
    else:
        arr_id = ID(f"{action_id}_data", is_declaration=True, type=cg.uint8)
        arr = cg.static_const_array(arr_id, cg.ArrayInitializer(*data))
        cg.add(var.set_data_static(arr, len(data)))
    return var
