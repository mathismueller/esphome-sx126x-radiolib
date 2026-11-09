#include "sx126x_radiolib.h"

#include <RadioLib.h>

#if defined(ESP_PLATFORM) && !defined(ARDUINO)
#include "driver/gpio.h"
#include "esp_err.h"
#include "esp_intr_alloc.h"
#else
#include <SPI.h>
#endif

#include "esphome/core/log.h"

namespace esphome::sx126x_radiolib {

static const char *const TAG = "sx126x_radiolib";

void IRAM_ATTR SX126xRadioLib::gpio_intr(void *arg) { static_cast<SX126xRadioLib *>(arg)->dio1_flag_ = true; }

void SX126xRadioLib::setup() {
  ESP_LOGCONFIG(TAG, "Setting up SX126x via RadioLib...");

#if defined(ESP_PLATFORM) && !defined(ARDUINO)
  // Native IDF HAL: EspHal owns the spi_master bus (SPI2_HOST, 2 MHz
  // default, software CS) and GPIO via IDF drivers. RadioLib.h pulls in
  // EspHal.h automatically for generic ESP_PLATFORM builds.
  this->hal_ = new EspHal(static_cast<int8_t>(this->sck_pin_), static_cast<int8_t>(this->miso_pin_),
                          static_cast<int8_t>(this->mosi_pin_));
  this->radio_ = new SX1262(new Module(this->hal_, this->cs_pin_, this->dio1_pin_, this->rst_pin_, this->busy_pin_));
#else
  SPI.begin(this->sck_pin_, this->miso_pin_, this->mosi_pin_, this->cs_pin_);

  this->radio_ = new SX1262(new Module(this->cs_pin_, this->dio1_pin_, this->rst_pin_, this->busy_pin_));
#endif

  // MCU-driven antenna switch pins (e.g. Wio-SX1262 header board RF_SW).
  // RadioLib drives these automatically on every TX/RX/standby transition.
  uint32_t rxen = this->has_rxen_pin_ ? this->rxen_pin_ : RADIOLIB_NC;
  uint32_t txen = this->has_txen_pin_ ? this->txen_pin_ : RADIOLIB_NC;
  this->radio_->setRfSwitchPins(rxen, txen);

  int16_t state;
  if (this->fsk_mode_) {
    // NOTE: SX1262::beginFSK takes frequency FIRST (unlike the base-class
    // order) - passing bitrate here silently tunes 4.8 MHz and fails.
    state = this->radio_->beginFSK(this->frequency_ / 1e6, this->bitrate_bps_ / 1000.0f, this->deviation_hz_ / 1000.0f,
                                   this->bandwidth_khz_, this->pa_power_, this->preamble_size_);
  } else {
    state = this->radio_->begin(this->frequency_ / 1e6);
  }
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
  if (this->fsk_mode_) {
    this->radio_->setBandwidth(this->bandwidth_khz_);
    if (this->sync_value_.size() == 1) {
      this->radio_->setSyncWord(this->sync_value_[0]);
    } else {
      this->radio_->setSyncWord(this->sync_value_.data(), this->sync_value_.size());
    }
    this->radio_->setDataShaping(this->shaping_);
    this->radio_->setWhitening(this->whitening_enable_, this->whitening_initial_);
    if (this->crc_enable_) {
      this->radio_->setCRC(this->crc_size_, this->crc_initial_, this->crc_polynomial_, this->crc_inverted_);
    } else {
      this->radio_->setCRC(0);
    }
    if (this->payload_length_ > 0) {
      this->radio_->fixedPacketLengthMode(this->payload_length_);
    } else {
      this->radio_->variablePacketLengthMode();
    }
  } else {
    this->radio_->setBandwidth(this->bandwidth_khz_);
    this->radio_->setSpreadingFactor(this->spreading_factor_);
    this->radio_->setCodingRate(this->coding_rate_);
    if (this->sync_value_.size() == 1) {
      this->radio_->setSyncWord(this->sync_value_[0]);
    } else {
      this->radio_->setSyncWord(this->sync_value_.data(), this->sync_value_.size());
    }
    // LoRa CRC: length 2 = on, 0 = off.
    this->radio_->setCRC(this->crc_enable_ ? 2 : 0);
  }
  this->radio_->setPreambleLength(this->preamble_size_);
  this->radio_->setOutputPower(this->pa_power_);
  this->radio_->setPaRampTime(this->pa_ramp_);
  this->radio_->setDio2AsRfSwitch(this->rf_switch_);

  // DIO1 interrupt latches on packet arrival; loop() drains it.
#if defined(ESP_PLATFORM) && !defined(ARDUINO)
  gpio_config_t io_conf = {};
  io_conf.pin_bit_mask = (1ULL << this->dio1_pin_);
  io_conf.mode = GPIO_MODE_INPUT;
  io_conf.pull_up_en = GPIO_PULLUP_DISABLE;
  io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
  io_conf.intr_type = GPIO_INTR_POSEDGE;
  if (gpio_config(&io_conf) != ESP_OK) {
    ESP_LOGE(TAG, "gpio_config(DIO1=%d) failed", this->dio1_pin_);
    this->mark_failed();
    return;
  }
  // EspHal::init() (run inside radio.begin()) already installs the ISR
  // service, so just add our handler; if the service is missing (future
  // RadioLib change), install it and retry instead of spamming the log.
  esp_err_t isr_add = gpio_isr_handler_add(static_cast<gpio_num_t>(this->dio1_pin_),
                                           reinterpret_cast<gpio_isr_t>(&SX126xRadioLib::gpio_intr), this);
  if (isr_add == ESP_ERR_INVALID_STATE) {
    esp_err_t isr_svc = gpio_install_isr_service(ESP_INTR_FLAG_IRAM);
    if (isr_svc != ESP_OK && isr_svc != ESP_ERR_INVALID_STATE) {
      ESP_LOGE(TAG, "gpio_install_isr_service failed: %s", esp_err_to_name(isr_svc));
      this->mark_failed();
      return;
    }
    isr_add = gpio_isr_handler_add(static_cast<gpio_num_t>(this->dio1_pin_),
                                   reinterpret_cast<gpio_isr_t>(&SX126xRadioLib::gpio_intr), this);
  }
  if (isr_add != ESP_OK) {
    ESP_LOGE(TAG, "gpio_isr_handler_add(DIO1=%d) failed: %s", this->dio1_pin_, esp_err_to_name(isr_add));
    this->mark_failed();
    return;
  }
#else
  attachInterruptArg(this->dio1_pin_, gpio_intr, this, RISING);
#endif

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
  ESP_LOGCONFIG(TAG, "  NSS=%d SCK=%d MOSI=%d MISO=%d", this->cs_pin_, this->sck_pin_, this->mosi_pin_,
                this->miso_pin_);
  ESP_LOGCONFIG(TAG, "  DIO1=%d BUSY=%d RST=%d", this->dio1_pin_, this->busy_pin_, this->rst_pin_);
  ESP_LOGCONFIG(TAG, "  RXEN pin=%d TXEN pin=%d DIO2-switch=%s", this->has_rxen_pin_ ? (int) this->rxen_pin_ : -1,
                this->has_txen_pin_ ? (int) this->txen_pin_ : -1, this->rf_switch_ ? "yes" : "no");
  ESP_LOGCONFIG(TAG, "  freq=%.3f MHz BW=%.1f kHz mode=%s SF=%d CR=4/%d", this->frequency_ / 1e6, this->bandwidth_khz_,
                this->fsk_mode_ ? "FSK" : "LORA", this->spreading_factor_, this->coding_rate_);
  if (this->fsk_mode_) {
    ESP_LOGCONFIG(TAG, "  bitrate=%u bps deviation=%u Hz shaping=0x%02X CRC len=%d whitening=%s",
                  (unsigned) this->bitrate_bps_, (unsigned) this->deviation_hz_, this->shaping_,
                  this->crc_enable_ ? this->crc_size_ : 0, this->whitening_enable_ ? "on" : "off");
  }
  ESP_LOGCONFIG(TAG, "  preamble=%d power=%d dBm crc=%s tcxo=%.1f V", this->preamble_size_, this->pa_power_,
                this->crc_enable_ ? "on" : "off", this->tcxo_voltage_);
}

}  // namespace esphome::sx126x_radiolib
