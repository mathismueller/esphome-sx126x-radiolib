import esphome.codegen as cg
from esphome.components.packet_transport import (
    PacketTransport,
    new_packet_transport,
    transport_schema,
)
import esphome.config_validation as cv
from esphome.cpp_generator import MockObj
from esphome.types import ConfigType

from .. import CONF_SX126X_RADIOLIB_ID, SX126xRadioLib, sx126x_radiolib_ns

SX126xRadioLibListener = sx126x_radiolib_ns.class_("SX126xRadioLibListener")
SX126xRadioLibTransport = sx126x_radiolib_ns.class_(
    "SX126xRadioLibTransport", PacketTransport, cg.PollingComponent, SX126xRadioLibListener
)

CONFIG_SCHEMA = transport_schema(SX126xRadioLibTransport).extend(
    {
        cv.GenerateID(CONF_SX126X_RADIOLIB_ID): cv.use_id(SX126xRadioLib),
    }
)


async def to_code(config: ConfigType) -> MockObj:
    var, _ = await new_packet_transport(config)
    radio = await cg.get_variable(config[CONF_SX126X_RADIOLIB_ID])
    cg.add(var.set_parent(radio))
    return var
