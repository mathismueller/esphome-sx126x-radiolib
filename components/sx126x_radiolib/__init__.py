from typing import Any

from esphome import automation, pins
import esphome.codegen as cg
from esphome.components.const import CONF_CRC_ENABLE, CONF_ON_PACKET
import esphome.config_validation as cv
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

# LoRa bandwidths only (FSK is not implemented yet, see validate_config).
BW_KHZ = {
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
    raise cv.Invalid(
        "data must either be a string wrapped in quotes or a list of bytes"
    )


def validate_config(config: ConfigType) -> ConfigType:
    if config[CONF_PREAMBLE_SIZE] < 6:
        raise cv.Invalid("Minimum 'preamble_size' is 6 with LORA")
    if config[CONF_SPREADING_FACTOR] < 7:
        raise cv.Invalid(
            "Spreading factor 6 (implicit header mode) is not supported yet, use 7-12"
        )
    if len(config[CONF_SYNC_VALUE]) > 2:
        raise cv.Invalid("'sync_value' takes at most 2 bytes with LORA")
    return config


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
            cv.Required(CONF_MODULATION): cv.one_of("LORA", upper=True),
            cv.Optional(CONF_ON_PACKET): automation.validate_automation(single=True),
            cv.Optional(CONF_BANDWIDTH, default="125_0kHz"): cv.enum(BW_KHZ),
            cv.Optional(CONF_CODING_RATE, default="CR_4_5"): cv.enum(CODING_RATE),
            cv.Optional(CONF_CRC_ENABLE, default=True): cv.boolean,
            cv.Optional(CONF_PA_POWER, default=14): cv.int_range(min=-3, max=22),
            cv.Optional(CONF_PA_RAMP, default="40us"): cv.enum(RAMP),
            cv.Optional(CONF_PAYLOAD_LENGTH, default=0): cv.int_range(min=0, max=255),
            cv.Optional(CONF_PREAMBLE_SIZE, default=8): cv.int_range(min=1, max=65535),
            cv.Optional(CONF_RX_START, default=True): cv.boolean,
            cv.Optional(CONF_SPREADING_FACTOR, default=9): cv.int_range(min=6, max=12),
            cv.Optional(CONF_SYNC_VALUE, default=[0x12]): cv.ensure_list(
                cv.hex_uint8_t
            ),
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
    cg.add(var.set_coding_rate(config[CONF_CODING_RATE]))
    cg.add(var.set_crc_enable(config[CONF_CRC_ENABLE]))
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
