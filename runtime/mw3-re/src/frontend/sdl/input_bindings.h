#pragma once

#include <algorithm>
#include <array>
#include <charconv>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include "gamez/zinput/zinput.h"

namespace sdlfe {

class InputBindingConfig {
 public:
  static constexpr size_t kCommandCount = 167;
  static constexpr size_t kMaxCombos = 64;

  static InputBindingConfig read_file(const std::string& path) {
    constexpr size_t limit = 65536;
    std::ifstream file(std::filesystem::u8path(path), std::ios::binary);
    if (!file) throw std::runtime_error("Cannot open MW3 input bindings: " + path);
    std::string bytes(limit + 1, '\0');
    file.read(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    if (file.bad() || (!file.eof() && file.fail()))
      throw std::runtime_error("Cannot read MW3 input bindings: " + path);
    if (file.gcount() > static_cast<std::streamsize>(limit))
      throw std::runtime_error("MW3 input bindings exceed 64 KiB");
    bytes.resize(static_cast<size_t>(file.gcount()));

    InputBindingConfig config;
    std::string_view remaining(bytes);
    bool header = false;
    while (!remaining.empty()) {
      const size_t end = remaining.find('\n');
      auto line = remaining.substr(0, end);
      if (end != remaining.npos && !line.empty() && line.back() == '\r') line.remove_suffix(1);
      remaining.remove_prefix(end == remaining.npos ? remaining.size() : end + 1);
      const auto kind = token(line);
      if (kind.empty()) continue;
      if (!header) {
        if (kind != "CC_MW3_INPUT_V1") throw std::runtime_error("Unknown MW3 input header");
        header = true;
      } else {
        config.read_binding(kind, line);
      }
      if (!token(line).empty()) throw std::runtime_error("Unexpected MW3 input fields");
    }
    if (!header) throw std::runtime_error("Missing MW3 input header");
    return config;
  }

  size_t binding_count() const { return combos_.size() + mouse_count_; }
  uint32_t mouse_wheel_mask() const { return wheel_mask_; }
  bool has_command_binding(int32_t cmd) const {
    return cmd > 0 && static_cast<size_t>(cmd) < commands_.size() && commands_[cmd];
  }

 private:
  friend class InputBindingState;
  struct Input {
    bool mouse = false;
    unsigned id = 0;
  };
  struct Combo {
    unsigned command, count;
    bool suppress;
    std::array<Input, 3> inputs{};
  };
  std::vector<Combo> combos_;
  std::array<unsigned, 8> mouse_commands_{};
  std::array<bool, kCommandCount> commands_{};
  size_t mouse_count_ = 0;
  uint32_t wheel_mask_ = 0;

  // Only space and tab separate fields. Comments and inline CR are invalid.
  static std::string_view token(std::string_view& line) {
    const size_t start = line.find_first_not_of(" \t");
    if (start == line.npos) return {};
    line.remove_prefix(start);
    auto field = line.substr(0, line.find_first_of(" \t"));
    line.remove_prefix(field.size());
    return field;
  }

  static unsigned number(std::string_view field, unsigned low, unsigned high, int base = 10) {
    if (base == 16 && (field.substr(0, 2) == "0x" || field.substr(0, 2) == "0X"))
      field.remove_prefix(2);
    if (field.empty()) throw std::runtime_error("Missing MW3 input number");
    unsigned value = 0;
    const auto end = field.data() + field.size();
    const auto result = std::from_chars(field.data(), end, value, base);
    if (result.ec != std::errc{} || result.ptr != end || value < low || value > high)
      throw std::runtime_error("Invalid MW3 input number: " + std::string(field));
    return value;
  }

  static Input physical_input(std::string_view field) {
    if (field.substr(0, 2) == "M:") return {true, number(field.substr(2), 1, 7)};
    if (field.substr(0, 2) != "K:") throw std::runtime_error("Expected K: or M: in MW3 combo");
    unsigned scan = number(field.substr(2), 1, 255, 16);
    if (scan == 0x43 || scan == 0x44 || scan == 0x57)
      throw std::runtime_error("Reserved scan code in MW3 combo");
    return {false, scan};
  }

  static uint32_t wheel_bit(unsigned id) { return id >= 6 ? 1u << (id - 6) : 0u; }

  void read_binding(std::string_view kind, std::string_view& line) {
    const unsigned command = number(token(line), 1, kCommandCount - 1);
    commands_[command] = true;
    if (kind == "MOUSE") {
      const unsigned id = number(token(line), 4, 7);
      if (mouse_commands_[id]) throw std::runtime_error("Duplicate MW3 mouse binding");
      mouse_commands_[id] = command;
      ++mouse_count_;
      wheel_mask_ |= wheel_bit(id);
      return;
    }
    if (kind != "COMBO") throw std::runtime_error("Unknown MW3 input row");
    if (combos_.size() == kMaxCombos) throw std::runtime_error("Too many MW3 combos");
    const auto flag = token(line);
    if (flag != "0" && flag != "1") throw std::runtime_error("Expected MW3 suppression flag 0 or 1");
    const bool suppress = flag == "1";
    Combo combo{command, number(token(line), 2, 3), suppress};
    uint32_t wheels = 0;
    for (unsigned i = 0; i < combo.count; ++i) {
      const Input input = physical_input(token(line));
      for (unsigned j = 0; j < i; ++j) {
        if (combo.inputs[j].id == input.id && combo.inputs[j].mouse == input.mouse)
          throw std::runtime_error("Repeated physical input in MW3 combo");
      }
      combo.inputs[i] = input;
      if (input.mouse) wheels |= wheel_bit(input.id);
    }
    if (wheels == 3) throw std::runtime_error("Opposing wheels in MW3 combo");
    wheel_mask_ |= wheels;
    combos_.push_back(combo);
  }
};

class WheelNotchQueue {
 public:
  static constexpr unsigned kMaxWheelNotches = 4;
  void enqueue(unsigned count) { pending_ += std::min(count, kMaxWheelNotches - pending_); }
  bool poll() {
    down_ = !down_ && pending_ != 0;
    if (down_) --pending_;
    return down_;
  }

 private:
  unsigned pending_ = 0;
  bool down_ = false;
};

// Reset when replacing the configuration: held history is indexed by binding.
class InputBindingState {
 public:
  using Keys = std::array<bool, 256>;
  using Buttons = std::array<bool, 6>;  // physical buttons 1..5
  void reset_transients() { *this = {}; }
  void enqueue_wheel(unsigned mouse_id, unsigned count = 1) {
    if (mouse_id == 6 || mouse_id == 7) wheel_[mouse_id - 6].enqueue(count);
  }
  bool key_suppressed(uint32_t scan) const { return scan < 256 && key_suppressed_[scan]; }
  bool mouse_suppressed(unsigned id) const { return id < 8 && mouse_suppressed_[id]; }
  bool mouse_input_down(unsigned id) const { return id < 8 && mouse_down_[id]; }
  bool extended_command_pressed(unsigned cmd) const {
    return cmd < extended_pressed_.size() && extended_pressed_[cmd];
  }
  std::array<uint32_t, InputBindingConfig::kCommandCount> actions{};

  void evaluate(const InputBindingConfig& config, const Keys& keys, const Buttons& buttons,
                bool text_entry, bool commands_enabled) {
    if (text_entry || !commands_enabled) {
      reset_transients();
      return;
    }
    std::copy(buttons.begin() + 1, buttons.end(), mouse_down_.begin() + 1);
    mouse_down_[6] = wheel_[0].poll();
    mouse_down_[7] = wheel_[1].poll();
    key_suppressed_.fill(false);
    mouse_suppressed_.fill(false);
    extended_pressed_.fill(false);
    std::array<bool, InputBindingConfig::kCommandCount> down{};
    auto record = [&](unsigned cmd, bool active, bool& was_down) {
      if (active) {
        down[cmd] = true;
        if (!was_down) extended_pressed_[cmd] = true;
      }
      was_down = active;
    };

    // Finish every chord before filtering any single button.
    for (size_t i = 0; i < config.combos_.size(); ++i) {
      const auto& combo = config.combos_[i];
      const auto end = combo.inputs.begin() + combo.count;
      const bool active = std::all_of(combo.inputs.begin(), end, [&](const auto& input) {
        return input.mouse ? mouse_down_[input.id] : keys[input.id];
      });
      record(combo.command, active, combo_was_down_[i]);
      if (active && combo.suppress) {
        for (auto it = combo.inputs.begin(); it != end; ++it) {
          if (it->mouse) mouse_suppressed_[it->id] = true;
          else key_suppressed_[it->id] = true;
        }
      }
    }
    for (unsigned id = 4; id <= 7; ++id) {
      const unsigned cmd = config.mouse_commands_[id];
      if (!cmd) continue;
      // A button held through a chord's release has no new physical press.
      if (mouse_suppressed_[id]) mouse_was_down_[id] = mouse_down_[id];
      else record(cmd, mouse_down_[id], mouse_was_down_[id]);
    }
    for (size_t cmd = 1; cmd < actions.size(); ++cmd) {
      const bool held = actions[cmd] == zin::kHeld || actions[cmd] == zin::kPressed;
      if (down[cmd]) actions[cmd] = held ? zin::kHeld : zin::kPressed;
      else actions[cmd] = held ? zin::kReleased : 0;
    }
  }

 private:
  std::array<WheelNotchQueue, 2> wheel_{};
  std::array<bool, InputBindingConfig::kMaxCombos> combo_was_down_{};
  std::array<bool, 8> mouse_down_{}, mouse_was_down_{}, mouse_suppressed_{};
  Keys key_suppressed_{};
  std::array<bool, InputBindingConfig::kCommandCount> extended_pressed_{};
};

}  // namespace sdlfe
