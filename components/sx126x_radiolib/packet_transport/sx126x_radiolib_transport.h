#pragma once

#include "esphome/core/automation.h"
#include "esphome/core/component.h"
#include "../sx126x_radiolib.h"
#include "esphome/components/packet_transport/packet_transport.h"
#include <vector>

namespace esphome::sx126x_radiolib {

class SX126xRadioLibTransport final : public packet_transport::PacketTransport,
                                      public Parented<SX126xRadioLib>,
                                      public SX126xRadioLibListener {
 public:
  void setup() override;
  void on_packet(const std::vector<uint8_t> &packet, float rssi, float snr) override;
  float get_setup_priority() const override { return setup_priority::AFTER_WIFI; }

 protected:
  void send_packet(const std::vector<uint8_t> &buf) const override;
  bool should_send() override { return true; }
  size_t get_max_packet_size() override;
};

}  // namespace esphome::sx126x_radiolib
