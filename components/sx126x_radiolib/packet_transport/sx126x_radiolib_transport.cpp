#include "sx126x_radiolib_transport.h"

#include "esphome/core/log.h"

namespace esphome::sx126x_radiolib {

static const char *const TAG = "sx126x_radiolib_transport";

void SX126xRadioLibTransport::setup() {
  PacketTransport::setup();
  this->parent_->register_listener(this);
}

void SX126xRadioLibTransport::send_packet(const std::vector<uint8_t> &buf) const {
  this->parent_->transmit_packet(buf);
}

void SX126xRadioLibTransport::on_packet(const std::vector<uint8_t> &packet, float rssi, float snr) {
  this->process_(packet);
}

size_t SX126xRadioLibTransport::get_max_packet_size() { return this->parent_->get_max_packet_size(); }

}  // namespace esphome::sx126x_radiolib
