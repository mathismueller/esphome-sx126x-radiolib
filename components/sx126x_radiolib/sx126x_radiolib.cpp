#include "sx126x_radiolib.h"

#include <RadioLib.h>
#include <SPI.h>

#include "esphome/core/log.h"

namespace esphome::sx126x_radiolib {

static const char *const TAG = "sx126x_radiolib";

void IRAM_ATTR SX126xRadioLib::gpio_intr(void *arg) {
  static_cast<SX126xRadioLib *>(arg)->dio1_flag_ = true;
}

void SX126xRadioLib::setup() {
  ESP_LOGCONFIG(TAG, "Setting up SX126x via RadioLib...");

  SPI.begin(this->sck_pin_, this->miso_pin_, this->mosi_pin_, this->cs_pin_);

  this->radio_ = new SX1262(new Module(this->cs_pin_, this->dio1_pin_, this->rst_pin_,
                                       this->busy_pin_));

  // MCU-driven antenna switch pins (e.g. Wio-SX1262 header board RF_SW).
  // RadioLib drives these automatically on every TX/RX/standby transition.
  uint32_t rxen = this->has_rxen_pin_ ? this->rxen_pin_ : RADIOLIB_NC;
  uint32_t txen = this->has_txen_pin_ ? this->txen_pin_ : RADIOLIB_NC;
  this->radio_->setRfSwitchPins(rxen, txen);

  int16_t state = this->radio_->begin(this->frequency_ / 1e6);
  if (state != RADIOLIB_ERR_NONE) {
    ESP_LOGE(TAG, "radio.begin() failed, code %d", state);
    this->mark_failed();
    return;
  }
  if (this->tcxo_voltage_ > 0.0f) {
    state = this->radio_->setTCXO(this->tcxo_voltage_);
    if (state != RADIOLIB_ERR_NONE) {
      ESP_LOGE(TAG, "setTCXO() failed, code %d", state);
      this->mark_failed();
      return;
    }
  }
  this->radio_->setFrequency(this->frequency_ / 1e6);
  this->radio_->setBandwidth(this->bandwidth_khz_);
  this->radio_->setSpreadingFactor(this->spreading_factor_);
  this->radio_->setCodingRate(this->coding_rate_);
  if (this->sync_value_.size() == 1) {
    this->radio_->setSyncWord(this->sync_value_[0]);
  } else {
    this->radio_->setSyncWord(this->sync_value_.data(), this->sync_value_.size());
  }
  this->radio_->setPreambleLength(this->preamble_size_);
  this->radio_->setOutputPower(this->pa_power_);
  this->radio_->setPaRampTime(this->pa_ramp_);
  // LoRa CRC: length 2 = on, 0 = off.
  this->radio_->setCRC(this->crc_enable_ ? 2 : 0);
  this->radio_->setDio2AsRfSwitch(this->rf_switch_);

  // DIO1 interrupt latches on packet arrival; loop() drains it.
  attachInterruptArg(this->dio1_pin_, gpio_intr, this, RISING);

  if (this->rx_start_) {
    this->start_rx_();
  }
  ESP_LOGCONFIG(TAG, "radio ready");
}

void SX126xRadioLib::start_rx_() {
  this->dio1_flag_ = false;
  int16_t state = this->radio_->startReceive();
  if (state != RADIOLIB_ERR_NONE) {
    ESP_LOGW(TAG, "startReceive() failed, code %d", state);
    this->rx_active_ = false;
    return;
  }
  this->rx_active_ = true;
}

void SX126xRadioLib::handle_rx_() {
  this->dio1_flag_ = false;
  // NOTE: getPacketLength() must be called BEFORE readData().
  size_t len = this->radio_->getPacketLength();
  if (len > RADIOLIB_SX126X_MAX_PACKET_LENGTH) {
    len = RADIOLIB_SX126X_MAX_PACKET_LENGTH;
  }
  uint8_t buf[RADIOLIB_SX126X_MAX_PACKET_LENGTH];
  int16_t state = this->radio_->readData(buf, len);
  if (state == RADIOLIB_ERR_NONE) {
    std::vector<uint8_t> packet(buf, buf + len);
    float rssi = this->radio_->getRSSI();
    float snr = this->radio_->getSNR();
    ESP_LOGD(TAG, "packet received, len=%u rssi=%.1f snr=%.1f", (unsigned) len, rssi, snr);
    this->packet_trigger_.trigger(packet, rssi, snr);
    for (auto *listener : this->listeners_) {
      listener->on_packet(packet, rssi, snr);
    }
  } else if (state == RADIOLIB_ERR_CRC_MISMATCH) {
    ESP_LOGD(TAG, "packet CRC mismatch, dropped");
  } else if (state != RADIOLIB_ERR_RX_TIMEOUT) {
    ESP_LOGW(TAG, "readData() failed, code %d", state);
  }
  // Re-arm RX (readData leaves the radio in standby).
  if (this->rx_start_) {
    this->start_rx_();
  } else {
    this->rx_active_ = false;
  }
}

void SX126xRadioLib::loop() {
  if (this->is_failed() || this->radio_ == nullptr) {
    return;
  }
  if (this->dio1_flag_) {
    this->handle_rx_();
  }
}

int SX126xRadioLib::transmit_packet(const std::vector<uint8_t> &packet) {
  if (this->is_failed() || this->radio_ == nullptr) {
    return RADIOLIB_ERR_UNKNOWN;
  }
  this->dio1_flag_ = false;
  int16_t state = this->radio_->transmit(packet.data(), packet.size());
  if (state != RADIOLIB_ERR_NONE) {
    ESP_LOGW(TAG, "transmit() failed, code %d", state);
  }
  if (this->rx_start_) {
    this->start_rx_();
  } else {
    this->rx_active_ = false;
  }
  return state;
}

void SX126xRadioLib::set_mode_rx() {
  if (this->rx_active_) {
    return;
  }
  this->start_rx_();
}

void SX126xRadioLib::set_mode_tx() {
  // Next transmit_packet() call switches to TX; nothing to do eagerly.
  this->rx_active_ = false;
  this->radio_->standby();
}

void SX126xRadioLib::set_mode_standby() {
  this->rx_active_ = false;
  this->radio_->standby();
}

void SX126xRadioLib::set_mode_sleep() {
  this->rx_active_ = false;
  this->radio_->sleep();
}

void SX126xRadioLib::dump_config() {
  ESP_LOGCONFIG(TAG, "SX126x via RadioLib:");
  ESP_LOGCONFIG(TAG, "  NSS=%d SCK=%d MOSI=%d MISO=%d", this->cs_pin_, this->sck_pin_,
                this->mosi_pin_, this->miso_pin_);
  ESP_LOGCONFIG(TAG, "  DIO1=%d BUSY=%d RST=%d", this->dio1_pin_, this->busy_pin_, this->rst_pin_);
  ESP_LOGCONFIG(TAG, "  RXEN pin=%d TXEN pin=%d DIO2-switch=%s", this->has_rxen_pin_ ? (int) this->rxen_pin_ : -1,
                this->has_txen_pin_ ? (int) this->txen_pin_ : -1, this->rf_switch_ ? "yes" : "no");
  ESP_LOGCONFIG(TAG, "  freq=%.3f MHz BW=%.1f kHz SF=%d CR=4/%d", this->frequency_ / 1e6,
                this->bandwidth_khz_, this->spreading_factor_, this->coding_rate_ - 4);
  ESP_LOGCONFIG(TAG, "  preamble=%d power=%d dBm crc=%s tcxo=%.1f V", this->preamble_size_,
                this->pa_power_, this->crc_enable_ ? "on" : "off", this->tcxo_voltage_);
}

}  // namespace esphome::sx126x_radiolib
