#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <istream>
#include <stdexcept>
#include <string>

namespace sdlfe {

struct ControllerAxisCalibration {
  double minimum = -32768, center = 0, maximum = 32767, deadzone = .12, response = 1;
  bool inverted = false;

  void validate(bool trigger) const {
    if (!std::isfinite(minimum) || !std::isfinite(center) || !std::isfinite(maximum) ||
        !std::isfinite(deadzone) || !std::isfinite(response) || minimum < -32768 || maximum > 32767 ||
        deadzone < 0 || deadzone > .45 || response < .25 || response > 4 ||
        (trigger ? center < 0 || maximum - center < 8192
                 : center - minimum < 8192 || maximum - center < 8192))
      throw std::runtime_error("Invalid controller calibration range");
  }

  double adjust(short raw, bool trigger) const {
    double value = trigger ? std::clamp((raw - center) / (maximum - center), 0.0, 1.0)
                           : std::clamp((raw - center) / (raw >= center ? maximum - center : center - minimum),
                                        -1.0, 1.0);
    value = std::copysign(std::pow(std::max(0.0, std::abs(value) - deadzone) / (1 - deadzone), response),
                          value);
    return inverted ? (trigger ? 1 - value : -value) : value;
  }
};

struct ControllerProfileConfig {
  std::string device;
  std::array<ControllerAxisCalibration, 6> calibration;
  std::array<unsigned, 26> buttons{};
  std::array<unsigned, 2> triggers{};
  std::array<int, 4> axes{1, 0, 2, 3};
  std::array<double, 4> scale{-1, 1, 1, 1};
  double threshold = .25;

  static ControllerProfileConfig read(std::istream& input) {
    ControllerProfileConfig config;
    std::string magic;
    input >> magic >> config.device;
    if (magic != "CC_MW3_CONTROLLER_V1" || config.device.size() != 64 ||
        config.device.find_first_not_of("0123456789abcdefABCDEF") != std::string::npos)
      throw std::runtime_error("Unknown MW3 controller config identity/version");
    std::transform(config.device.begin(), config.device.end(), config.device.begin(), [](char value) {
      return value >= 'a' && value <= 'f' ? static_cast<char>(value - 'a' + 'A') : value;
    });
    for (size_t i = 0; i < config.calibration.size(); ++i) {
      int inverted = 0;
      auto& axis = config.calibration[i];
      input >> axis.minimum >> axis.center >> axis.maximum >> axis.deadzone >> axis.response >> inverted;
      if (!input || (inverted != 0 && inverted != 1)) throw std::runtime_error("Invalid controller calibration");
      axis.inverted = inverted != 0;
      axis.validate(i >= 4);
    }
    for (unsigned& command : config.buttons) {
      input >> command;
      if (!input || command > 166) throw std::runtime_error("Controller button command outside MW3 range");
    }
    for (unsigned& command : config.triggers) {
      input >> command;
      if (!input || command > 166) throw std::runtime_error("Controller trigger command outside MW3 range");
    }
    for (int& axis : config.axes) {
      input >> axis;
      if (!input || axis < -1 || axis > 3) throw std::runtime_error("Invalid controller stick assignment");
    }
    for (double& scale : config.scale) {
      input >> scale;
      if (!input || !std::isfinite(scale) || std::abs(scale) < .1 || std::abs(scale) > 2)
        throw std::runtime_error("Invalid controller sensitivity");
    }
    input >> config.threshold;
    if (!input || !std::isfinite(config.threshold) || config.threshold < .05 || config.threshold > .95)
      throw std::runtime_error("Incomplete controller config");
    input >> std::ws;
    if (!input.eof()) throw std::runtime_error("Unexpected controller config fields");
    return config;
  }
};

struct ControllerSample {
  std::array<short, 6> axes{};
  std::array<bool, 26> buttons{};
  bool connected = false, focused = false;
};

struct ControllerState {
  std::array<unsigned, 167> actions{};
  std::array<double, 4> analog{};
  bool armed = false, connected = false, throttle_stopped = false;

  void update(const ControllerProfileConfig& config, const ControllerSample& sample) {
    std::array<bool, 167> down{};
    std::array<double, 6> adjusted{};
    const bool available = sample.connected && sample.focused;
    bool neutral = true;
    for (size_t i = 0; i < adjusted.size(); ++i) {
      adjusted[i] = config.calibration[i].adjust(sample.axes[i], i >= 4);
      auto without_inversion = config.calibration[i];
      without_inversion.inverted = false;
      neutral = neutral && std::abs(without_inversion.adjust(sample.axes[i], i >= 4)) < .05;
      neutral = neutral && (i < 4 || adjusted[i] < .05);
    }
    for (bool held : sample.buttons) neutral = neutral && !held;
    if (!available) armed = false;
    else if (!armed && neutral) armed = true;
    connected = available && armed;
    analog.fill(0);
    if (connected) {
      for (size_t i = 0; i < sample.buttons.size(); ++i)
        if (sample.buttons[i] && config.buttons[i]) down[config.buttons[i]] = true;
      for (size_t i = 0; i < config.triggers.size(); ++i)
        if (adjusted[4 + i] >= config.threshold && config.triggers[i]) down[config.triggers[i]] = true;
      for (size_t i = 0; i < config.axes.size(); ++i)
        if (config.axes[i] >= 0) analog[i] = std::clamp(adjusted[config.axes[i]] * config.scale[i], -1.0, 1.0);
      if (down[27]) throttle_stopped = true;
      else if (std::abs(analog[0]) < .05) throttle_stopped = false;
      if (throttle_stopped) analog[0] = 0;
    }
    for (size_t i = 0; i < actions.size(); ++i) {
      const bool was_down = (actions[i] & 3) != 0;
      actions[i] = down[i] ? (was_down ? 2U : 1U) : (was_down ? 4U : 0U);
    }
  }
};

}  // namespace sdlfe
