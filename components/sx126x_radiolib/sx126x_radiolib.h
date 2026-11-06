#pragma once

#include <RadioLib.h>

#include "esphome/core/automation.h"
#include "esphome/core/component.h"
#include "esphome/core/hal.h"
#include <utility>
#include <vector>

namespace esphome::sx126x_radiolib {

class SX126xRadioLib final : public Component {
 public:
  float get_setup_priority() const override { return setup_priority::PROCESSOR; }
  void setup() override;
  void loop() override;
  void dump_config() override;

  void set_cs_pin(uint8_t pin) { this->cs_pin_ = pin; }
  void set_sck_pin(uint8_t pin) { this->sck_pin_ = pin; }
  void set_mosi_pin(uint8_t pin) { this->mosi_pin_ = pin; }
  void set_miso_pin(uint8_t pin) { this->miso_pin_ = pin; }
  void set_dio1_pin(uint8_t pin) { this->dio1_pin_ = pin; }
  void set_busy_pin(uint8_t pin) { this->busy_pin_ = pin; }
  void set_rst_pin(uint8_t pin) { this->rst_pin_ = pin; }
  void set_rxen_pin(uint8_t pin) {
    this->rxen_pin_ = pin;
    this->has_rxen_pin_ = true;
  }
  void set_txen_pin(uint8_t pin) {
    this->txen_pin_ = pin;
    this->has_txen_pin_ = true;
  }
  void set_bandwidth(float bandwidth_khz) { this->bandwidth_khz_ = bandwidth_khz; }
  void set_coding_rate(uint8_t coding_rate) { this->coding_rate_ = coding_rate; }
  void set_crc_enable(bool crc_enable) { this->crc_enable_ = crc_enable; }
  void set_frequency(uint32_t frequency) { this->frequency_ = frequency; }
  void set_hw_version(const std::string &hw_version) { this->hw_version_ = hw_version; }
  void set_pa_power(int8_t power) { this->pa_power_ = power; }
  void set_pa_ramp(uint8_t ramp) { this->pa_ramp_ = ramp; }
  void set_payload_length(uint8_t payload_length) { this->payload_length_ = payload_length; }
  void set_preamble_size(uint16_t preamble_size) { this->preamble_size_ = preamble_size; }
  void set_rf_switch(bool rf_switch) { this->rf_switch_ = rf_switch; }
  void set_spreading_factor(uint8_t spreading_factor) { this->spreading_factor_ = spreading_factor; }
  void set_sync_value(const std::vector<uint8_t> &sync_value) { this->sync_value_ = sync_value; }
  void set_rx_start(bool rx_start) { this->rx_start_ = rx_start; }
  void set_tcxo_voltage(float tcxo_voltage) { this->tcxo_voltage_ = tcxo_voltage; }
  void set_tcxo_delay(uint32_t tcxo_delay_us) { this->tcxo_delay_us_ = tcxo_delay_us; }

  void set_mode_rx();
  void set_mode_tx();
  void set_mode_standby();
  void set_mode_sleep();
  int transmit_packet(const std::vector<uint8_t> &packet);

  Trigger<std::vector<uint8_t>, float, float> *get_packet_trigger() { return &this->packet_trigger_; }

 protected:
  static void IRAM_ATTR gpio_intr(void *arg);
  void start_rx_();
  void handle_rx_();

  Trigger<std::vector<uint8_t>, float, float> packet_trigger_;

  // Raw GPIO numbers: RadioLib drives the pins itself through Arduino APIs.
  uint8_t cs_pin_{0};
  uint8_t sck_pin_{0};
  uint8_t mosi_pin_{0};
  uint8_t miso_pin_{0};
  uint8_t dio1_pin_{0};
  uint8_t busy_pin_{0};
  uint8_t rst_pin_{0};
  uint8_t rxen_pin_{0};
  uint8_t txen_pin_{0};
  bool has_rxen_pin_{false};
  bool has_txen_pin_{false};

  SX1262 *radio_{nullptr};
  volatile bool dio1_flag_{false};

  std::string hw_version_{"sx1262"};
  std::vector<uint8_t> sync_value_{0x12};
  float bandwidth_khz_{125.0};
  uint32_t frequency_{868000000};
  uint32_t tcxo_delay_us_{5000};
  uint16_t preamble_size_{8};
  float tcxo_voltage_{0.0f};
  uint8_t coding_rate_{5};
  uint8_t spreading_factor_{9};
  uint8_t payload_length_{0};
  uint8_t pa_ramp_{0x03};
  int8_t pa_power_{14};
  bool rx_start_{true};
  bool rf_switch_{true};
  bool crc_enable_{true};
  bool rx_active_{false};
};

}  // namespace esphome::sx126x_radiolib
