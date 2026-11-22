// mech3's controls setup on the real zInput map, and the fixes the
// differential test cannot reach (the original crashes or hangs there).
#include <cstdio>
#include <cstring>
#include <array>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>

#include "check.h"
#include "frontend/sdl/input_bindings.h"
#include "gamez/zutil/zfix.h"
#include "gamez/zinput/zinput.h"
#include "gamez/zreader/zreader.h"
#include "gamez/zutil/zutl_path.h"
#include "mech3/controls_cfg.h"
#include "gamez/zutil/zutl_reg.h"
#include "platform/reg_file.h"

namespace {
const std::string kDir = std::string(MW3_TEST_TMP) + "/test_controls";

void fresh() {
  zin::init(0xa7, "DefaultCmdMap");
  mech3::controls_setup() = mech3::ControlsSetup{};
  mech3::controls_setup_calls() = mech3::ControlsSetupCalls{};
  mech3::axis_table() = mech3::AxisTable{};
  zutl::mounts().read.clear();
  zutl::set_write_dir(kDir);
}

void write(const char* path, const std::string& text) {
  std::FILE* f = zutl::open(path, "wb");
  std::fwrite(text.data(), 1, text.size(), f);
  std::fclose(f);
}

std::string hex_value(const uint8_t* bytes, size_t size, const std::string& eol, bool wrapped) {
  std::ostringstream out;
  out << "hex:";
  for (size_t i = 0; i < size; ++i) {
    if (i) out << ',';
    if (wrapped && i && i % 24 == 0) out << "\\" << eol << "  ";
    out << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned>(bytes[i]);
  }
  return out.str();
}

class SettingsMapHost final : public zin::Host {
 public:
  explicit SettingsMapHost(uint32_t* map) : map_(map) {}
  uint32_t* settings_block(const char* name, uint32_t size) override {
    return std::strcmp(name, "DefaultCmdMap") == 0 && size == 167 * sizeof(uint32_t) ? map_ : nullptr;
  }

 private:
  uint32_t* map_;
};

constexpr int kZoomLock = 0x15, kNextWeapon = 0x25, kPreviousWeapon = 0x26;
std::array<int, 167> calls{};
void count_command(int32_t cmd) { ++calls[cmd]; }

class ScopedInput final : public platform::Input {
 public:
  ScopedInput() : saved_(std::move(zin::state())) {
    zin::reset_state();
    zin::init(167, "DefaultCmdMap");
    zin::state().di = this;
    zin::state().events.resize(128);
    zin::state().mouse_open = true;
    zin::state().mouse_acquired = 1;
    zin::state().mouse_flags = zin::state().kbd_flags = 1;
    zin::state().mouse_users = zin::state().kbd_users = 1;
    calls.fill(0);
    zfix::set_all(true);
  }
  ~ScopedInput() override {
    zin::state() = std::move(saved_);
    zfix::set_all(true);
    zfix::options() = saved_fixes_;
  }
  bool open(Device) override { return true; }
  void close(Device) override {}
  int32_t acquire(Device) override { return 0; }
  int32_t unacquire(Device) override { return 0; }
  void begin_poll(bool text, bool enabled) override {
    saw_text = text;
    saw_enabled = enabled;
    snapshot_mouse = mouse;
  }
  int32_t mouse_state(platform::MouseState* out) override {
    *out = snapshot_mouse;
    return 0;
  }
  int32_t keyboard_data(platform::KeyEvent* out, uint32_t* count) override {
    *count = static_cast<uint32_t>(events.size());
    std::copy(events.begin(), events.end(), out);
    events.clear();
    return 0;
  }
  int32_t joystick_state(platform::JoyState*) override { return 0; }
  bool command_has_extended_binding(int32_t cmd) const override { return cmd == 0x3d && extended_fire; }
  bool extended_command_pressed(int32_t cmd) const override {
    return weapon_edges && (cmd == kNextWeapon || cmd == kPreviousWeapon);
  }
  uint32_t command_state(int32_t cmd) override { return cmd == kNextWeapon ? overlay : 0; }
  bool key_suppressed(uint32_t scan) const override { return suppress && scan == 0x11; }
  bool mouse_suppressed(int32_t id) const override { return suppress && id == 3; }

  bool extended_fire = false, weapon_edges = false, suppress = false;
  bool saw_text = false, saw_enabled = false;
  uint32_t overlay = 0;
  platform::MouseState mouse{}, snapshot_mouse{};
  std::vector<platform::KeyEvent> events;

 private:
  zin::State saved_;
  zfix::Options saved_fixes_ = zfix::options();
};

const std::string kInputHeader = "CC_MW3_INPUT_V1\n";
sdlfe::InputBindingConfig read_fixture(const std::string& bytes) {
  std::filesystem::create_directories(kDir);
  const auto path = kDir + "/input.txt";
  {
    std::ofstream file(path, std::ios::binary);
    file.exceptions(std::ios::badbit | std::ios::failbit);
    file << bytes;
  }
  return sdlfe::InputBindingConfig::read_file(path);
}

template <class Read>
bool rejects(Read read) {
  try {
    read();
    return false;
  } catch (const std::runtime_error&) {
    return true;
  }
}

std::string parse(const std::string& text) {
  write("parse.zrd", text);
  zrdr::Node* root = zrdr::load("parse.zrd");
  if (!root) return "null";
  std::string out;
  for (int32_t i = 1; i < root->list[0].i; ++i) {
    const zrdr::Node& n = root->list[i];
    out += n.type == zrdr::String ? n.s : n.type == zrdr::List ? "(list)" : "#";
    out += ' ';
  }
  zrdr::free_node(root);
  return out;
}
}  // namespace

TEST(controls_defaults_save_and_load_round_trip) {
  fresh();
  EXPECT(mech3::controls_set_defaults() == 1);
  EXPECT(zin::key1_of(0x3d) == 0x39 && zin::joy_of(0x3d) == 1 && zin::mouse_of(0x3d) == 1);  // fire: Space
  EXPECT(zin::key1_of(1) == 0x13e);       // Quick Exit: Alt-F4
  EXPECT(zin::key1_of(0x71) == 0x210);    // Exit Mission: Ctrl-Q
  EXPECT(zin::key2_of(2) == 0xd2 && zin::key2_of(3) == 0xc9);  // Insert, Page Up: also the jets' rotations
  EXPECT(zin::key1_of(0x11) == 0xd2 && zin::key1_of(0x12) == 0xc9);
  EXPECT(mech3::controls_group_count() == 7);
  EXPECT(mech3::controls_command("CMD_TRIGGER1") == 0x3d);
  EXPECT(mech3::controls_setup().commands[0x18].axis_key == 1);
  mech3::axis_table().set(1, 9, 1.0f, 0.0f, 0.0f);  // twist on the mouse
  mech3::controls_save("keys\\mine.zrd");
  zin::bind(0x3d, nullptr, 0x1c, 0, 0, 0);
  mech3::axis_table() = mech3::AxisTable{};
  mech3::controls_load("keys\\mine.zrd");
  EXPECT(zin::key1_of(0x3d) == 0x39 && zin::joy_of(0x3d) == 1);
  EXPECT(zin::key1_of(1) == 0);  // not in the file: unbound, as in the original
  EXPECT(mech3::axis_table().axes[1].source == 9 && mech3::axis_table().axes[0].source == 3);
  EXPECT(mech3::axis_table().ready == 0 && mech3::axis_table().stock == 0);
}

// Playtest W40: a map saved with the quit box up (mouse button 1 on nothing,
// TRIGGER1 without a mouse button) gets the button back on TRIGGER1; maps the
// player rebound on purpose stay as they are.
TEST(controls_repair_mouse_fire_only_mends_the_quit_boxs_damage) {
  ScopedInput input;
  fresh();
  mech3::controls_set_defaults();
  EXPECT(!mech3::controls_repair_mouse_fire());  // the defaults: nothing to mend
  zin::bind_mouse(0, 0x3d);                       // as the quit box (0x0048e2d0) unbinds it
  EXPECT(zin::mouse_of(0x3d) == 0 && zin::mouse_command(1) == 0);
  input.extended_fire = true;
  EXPECT(!mech3::controls_repair_mouse_fire());
  EXPECT(zin::mouse_of(0x3d) == 0 && zin::mouse_command(1) == 0);
  input.extended_fire = false;
  EXPECT(mech3::controls_repair_mouse_fire());
  EXPECT(zin::mouse_of(0x3d) == 1 && zin::mouse_command(1) == 0x3d);
  EXPECT(zin::mouse_of(0x17) == 2 && zin::key1_of(0x3d) == 0x39);  // the rest untouched
  zin::bind_mouse(2, 0x3d);  // fire moved to the right button: button 1 on nothing
  EXPECT(!mech3::controls_repair_mouse_fire());
  EXPECT(zin::mouse_of(0x3d) == 2 && zin::mouse_command(1) == 0);
  mech3::controls_set_defaults();
  zin::bind_mouse(1, 0x17);  // button 1 on free look: fire has none
  EXPECT(!mech3::controls_repair_mouse_fire());
  EXPECT(zin::mouse_of(0x3d) == 0 && zin::mouse_command(1) == 0x17);
}

TEST(controls_stock_axes_and_missing_files) {
  fresh();
  mech3::controls_set_defaults();
  mech3::controls_save("keys\\stock.zrd");  // the table as it starts: the joystick's defaults
  mech3::controls_load("keys\\stock.zrd");
  EXPECT(mech3::axis_table().stock == 1);
  mech3::controls_load("keys\\nothing.zrd");  // no file: nothing changes
  EXPECT(mech3::axis_table().stock == 1 && zin::key1_of(0x3d) == 0x39);
}

TEST(launcher_settings_and_control_preset_match_runtime_readers) {
  struct EolCase { const char* eol; bool wrapped; };
  for (const EolCase fixture : {EolCase{"\r\n", true}, EolCase{"\r\n", false},
                                EolCase{"\n", true}, EolCase{"\n", false}}) {
    fresh();
    zreg::shutdown();
    const std::string eol = fixture.eol;
    uint32_t map[167] = {};
    const uint32_t command_binding = zin::pack(0x2c, 0x33, 4, 2);
    map[0x3d] = command_binding;
    std::array<uint8_t, sizeof map> map_bytes{};
    std::memcpy(map_bytes.data(), map, sizeof map);
    std::array<uint8_t, 260> active_bytes{};
    const std::string active_path = "keys\\CC-runtime-fixture.zrd";
    std::memcpy(active_bytes.data(), active_path.c_str(), active_path.size() + 1);

    const std::string reg_path = kDir + "/settings.reg";
    std::filesystem::create_directories(kDir);
    {
      std::ofstream reg(reg_path, std::ios::binary);
      reg << "Windows Registry Editor Version 5.00" << eol << eol
          << "[HKEY_CURRENT_USER\\SOFTWARE\\MicroProse\\MechWarrior 3\\1.0]" << eol
          << "\"DefaultCmdMap\"=" << hex_value(map_bytes.data(), map_bytes.size(), eol, fixture.wrapped) << eol
          << "\"ActiveCtlCfg\"=" << hex_value(active_bytes.data(), active_bytes.size(), eol, fixture.wrapped) << eol;
    }
    platform::RegFile settings(reg_path);
    zreg::init("MicroProse", "MechWarrior 3", "1.0", zreg::Machine{}, 0);
    zreg::set_settings(&settings);
    auto* map_entry = zreg::create("DefaultCmdMap", zreg::kBuffer, sizeof map, zreg::kUser,
                                   reinterpret_cast<uint8_t*>(map));
    uint8_t active_read[260] = {};
    zreg::create("ActiveCtlCfg", zreg::kBuffer, sizeof active_read, zreg::kUser, active_read);
    EXPECT(map_entry != nullptr);

    SettingsMapHost host(map);
    zin::reset_state();
    zin::set_host(&host);
    zin::init(0xa7, "DefaultCmdMap");
    EXPECT(zreg::read_all() == 1);
    EXPECT(map[0x3d] == zin::pack(0x2c, 0x33, 4, 2));
    EXPECT(zin::key1_of(0x3d) == 0x2c && zin::key2_of(0x3d) == 0x33 &&
           zin::joy_of(0x3d) == 4 && zin::mouse_of(0x3d) == 2);

    const std::string active_from_registry(reinterpret_cast<char*>(active_read));
    EXPECT(active_from_registry == active_path);  // ActiveCtlCfg already contains the keys\ prefix.
    write("keys\\CC-runtime-fixture.zrd",
          "(\n KEYS ((CMD_TRIGGER1 keya(0x2c) keyb(0x33) joybtn(0x4) mousebtn(0x2)))\n"
          " AXES ((Throttle joystick(Z) slope(-0.5) intercept(0.5) deadzone(0.05))\n"
          "       (Twist joystick(Rz) slope(-1) intercept(0) deadzone(0))\n"
          "       (Pitch joystick(Y) slope(1) intercept(0) deadzone(0))\n"
          "       (LR joystick(X) slope(-1) intercept(0) deadzone(0)))\n)\n");
    mech3::controls_setup() = mech3::ControlsSetup{};
    mech3::controls_setup_calls() = mech3::ControlsSetupCalls{};
    mech3::axis_table() = mech3::AxisTable{};
    EXPECT(mech3::controls_set_defaults() == 1);
    mech3::controls_load(active_from_registry.c_str());
    EXPECT(zin::key1_of(0x3d) == 0x2c && zin::key2_of(0x3d) == 0x33 &&
           zin::joy_of(0x3d) == 4 && zin::mouse_of(0x3d) == 2);
    EXPECT(mech3::axis_table().axes[0].source == 3 && mech3::axis_table().axes[0].scale == -0.5f &&
           mech3::axis_table().axes[0].offset == 0.5f && mech3::axis_table().axes[0].deadzone == 0.05f);
    EXPECT(mech3::axis_table().axes[1].source == 6 && mech3::axis_table().axes[2].source == 2 &&
           mech3::axis_table().axes[3].source == 1);
    zin::set_host(nullptr);
    zreg::set_settings(nullptr);
    zreg::shutdown();
  }
}

TEST(controls_file_fixes_skip_what_crashed_the_original) {
  fresh();
  mech3::controls_set_defaults();
  write("keys\\bad.zrd",
        "( KEYS ( 5 (7 keya(0x10)) () (CMD_JJ_UP keya(0x24)) )\n"
        "  AXES ( (Yaw joystick(Y) slope(2.0) deadzone(0.2)) (LR mouse(X)) x ) )\n");
  mech3::controls_load("keys\\bad.zrd");
  EXPECT(zin::key1_of(0xc) == 0x24);
  EXPECT(mech3::controls_group_count() == 7);  // the original wrote the Yaw entry over the groups' list
  EXPECT(mech3::axis_table().axes[3].source == 9);
  EXPECT(mech3::axis_table().axes[2].source == 0);
}

TEST(zreader_text_files) {
  fresh();
  EXPECT(parse("(a ; comment (\n b \"c d\" 5 e\"f\"g)") == "(list) ");
  EXPECT(parse("a (b") == "null");
  EXPECT(parse("x\n#ifdef DEBUG\ny\n#else\nz\n#endif\nw") == "x z ");  // w: the end of file drops it
  // FIX (bug): a token of 256 characters or more is dropped (the original
  // overwrote its return address), an open quote or #ifdef ends at the end.
  EXPECT(parse(std::string(300, 'q') + " k ") == "");  // the list ends there
  EXPECT(parse("a \"open") == "a ");
  EXPECT(parse("a\n#ifdef X\nb c ") == "a ");
  zrdr::state().if_depth = 0;
}

TEST(controls_input_file_format) {
  const auto config = read_fixture("\r\n CC_MW3_INPUT_V1\r\nMOUSE 1 4\nMOUSE 166 5\n"
                                   "MOUSE 37 6\nMOUSE 38 7\nCOMBO 13 1 2 K:11 K:0x39\r\n"
                                   "COMBO 15 0 3 M:1 K:01 K:FF");
  EXPECT(config.binding_count() == 6 && config.mouse_wheel_mask() == 3);
  for (int cmd : {1, 13, 15, 37, 38, 166}) EXPECT(config.has_command_binding(cmd));
  for (int cmd : {-1, 0, 165, 167}) EXPECT(!config.has_command_binding(cmd));
  EXPECT(read_fixture(kInputHeader + "COMBO 13 1 2 M:6 K:11").mouse_wheel_mask() == 1);
  EXPECT(read_fixture(kInputHeader + "COMBO 13 0 2 M:7 K:11").mouse_wheel_mask() == 2);
  auto boundary = kInputHeader + "MOUSE 37 6";
  boundary.resize(65536, ' ');
  EXPECT(read_fixture(boundary).binding_count() == 1);
  EXPECT(rejects([&] { read_fixture(boundary + " "); }));
  EXPECT(rejects([] { sdlfe::InputBindingConfig::read_file(kDir + "/missing-input"); }));
  EXPECT(rejects([] { sdlfe::InputBindingConfig::read_file(kDir); }));
  for (const auto* invalid : {"", " \n", "CC_MW3_INPUT_V2", "CC_MW3_INPUT_V1 extra",
                              "#comment\nCC_MW3_INPUT_V1"})
    EXPECT(rejects([&] { read_fixture(invalid); }));
  for (const auto* row : {
           "#comment", "KEY 1 4", "MOUSE", "MOUSE 1", "MOUSE 0 4", "MOUSE 167 4", "MOUSE -1 4",
           "MOUSE +1 4", "MOUSE 4294967296 4", "MOUSE 1x 4", "MOUSE 1 3", "MOUSE 1 8",
           "MOUSE 1 5x", "MOUSE 1 4 extra", "MOUSE 1\n4", "MOUSE 1 4\nMOUSE 2 4",
           "COMBO 0 1 2 M:1 M:2", "COMBO 167 1 2 M:1 M:2", "COMBO 1 2 2 M:1 M:2",
           "COMBO 1 1 1 M:1", "COMBO 1 1 4 M:1 M:2 M:3 M:4", "COMBO 1 1 3 M:1 M:2",
           "COMBO 1 1 2 M:1 M:2 M:3", "COMBO 1 1 2 K:0 M:1", "COMBO 1 1 2 K:0x100 M:1",
           "COMBO 1 1 2 K:0x43 M:1", "COMBO 1 1 2 K:0x44 M:1", "COMBO 1 1 2 K:0x57 M:1",
           "COMBO 1 1 2 K:0x M:1", "COMBO 1 1 2 K:1g M:1", "COMBO 1 1 2 X:2 M:1",
           "COMBO 1 1 2 K:100000000 M:1", "COMBO 1 1 2 M:0 M:1", "COMBO 1 1 2 M:1 M:8",
           "COMBO 1 1 2 K:11 K:0x11", "COMBO 1 1 2 M:1 M:1", "COMBO 1 1 3 M:7 K:11 M:6"})
    EXPECT(rejects([&] { read_fixture(kInputHeader + row); }));
  std::string rows = kInputHeader;
  for (int i = 1; i <= 64; ++i) {
    std::ostringstream row;
    row << "COMBO 1 0 2 M:1 K:" << std::hex << i << '\n';
    rows += row.str();
  }
  EXPECT(read_fixture(rows).binding_count() == 64);
  EXPECT(rejects([&] { read_fixture(rows + "COMBO 2 0 2 M:4 M:5"); }));
}

TEST(controls_input_chords_share_one_snapshot) {
  auto config = read_fixture(kInputHeader + "COMBO 13 1 2 K:11 K:39\nCOMBO 15 1 2 K:39 K:1E\n"
                             "COMBO 13 0 2 M:1 M:2\nMOUSE 13 4\nMOUSE 16 5\n"
                             "COMBO 17 1 3 M:5 K:39 K:1E");
  for (unsigned first : {0x11u, 0x39u}) {
    sdlfe::InputBindingState state;
    sdlfe::InputBindingState::Keys keys{};
    sdlfe::InputBindingState::Buttons mouse{};
    auto poll = [&] { state.evaluate(config, keys, mouse, false, true); };
    keys[first] = true;
    poll();
    EXPECT(state.actions[13] == 0 && !state.key_suppressed(first));
    keys[0x11] = keys[0x39] = keys[0x1e] = mouse[5] = true;
    poll();
    EXPECT(state.actions[13] == zin::kPressed && state.actions[15] == zin::kPressed);
    EXPECT(state.actions[17] == zin::kPressed && state.actions[16] == 0);
    EXPECT(state.key_suppressed(0x11) && state.key_suppressed(0x39) && state.key_suppressed(0x1e));
    EXPECT(state.mouse_suppressed(5) && state.mouse_input_down(5));
    poll();
    EXPECT(!state.extended_command_pressed(13));
    mouse[1] = mouse[2] = true;
    poll();
    EXPECT(state.actions[13] == zin::kHeld && state.extended_command_pressed(13));
    EXPECT(!state.mouse_suppressed(1) && !state.mouse_suppressed(2));
    mouse[4] = true;
    poll();
    EXPECT(state.actions[13] == zin::kHeld && state.extended_command_pressed(13));
    poll();
    EXPECT(!state.extended_command_pressed(13));
    keys.fill(false);
    mouse[1] = mouse[2] = mouse[4] = false;
    poll();
    EXPECT(state.actions[13] == zin::kReleased && !state.mouse_suppressed(5));
    EXPECT(state.actions[16] == zin::kPressed && !state.extended_command_pressed(16));
    EXPECT(!state.key_suppressed(0x39) && !state.extended_command_pressed(13));
    poll();
    EXPECT(state.actions[13] == 0);
  }
}

TEST(controls_input_wheel_edges_and_reset) {
  auto config = read_fixture(kInputHeader + "MOUSE 37 6\nMOUSE 38 7\nCOMBO 13 1 2 K:11 M:1");
  sdlfe::InputBindingState state;
  sdlfe::InputBindingState::Keys keys{};
  sdlfe::InputBindingState::Buttons buttons{};
  auto poll = [&] { state.evaluate(config, keys, buttons, false, true); };
  state.enqueue_wheel(6, ~0u);
  for (int i = 0; i < 9; ++i) {
    if (i == 1) state.enqueue_wheel(7);
    poll();
    const bool up = i < 8 && i % 2 == 0;
    EXPECT(state.mouse_input_down(6) == up && state.extended_command_pressed(37) == up);
    EXPECT(state.actions[37] == (up ? zin::kPressed : (i < 8 ? zin::kReleased : 0)));
    EXPECT(state.mouse_input_down(7) == (i == 1));
    EXPECT(state.actions[38] == (i == 1 ? zin::kPressed : (i == 2 ? zin::kReleased : 0)));
  }
  for (int reset = 0; reset < 3; ++reset) {
    keys[0x11] = buttons[1] = true;
    state.enqueue_wheel(6, 4);
    state.enqueue_wheel(7, 4);
    poll();
    EXPECT(state.extended_command_pressed(13) && state.mouse_suppressed(1));
    if (reset == 0) state.reset_transients();
    else state.evaluate(config, keys, buttons, reset == 1, reset != 2);
    EXPECT(state.actions[13] == 0 && !state.extended_command_pressed(13));
    EXPECT(!state.key_suppressed(0x11) && !state.mouse_suppressed(1));
    EXPECT(!state.mouse_input_down(6) && !state.mouse_input_down(7));
    poll();
    EXPECT(state.actions[13] == zin::kPressed && state.extended_command_pressed(13));
    EXPECT(state.actions[37] == 0 && state.actions[38] == 0);
    keys[0x11] = buttons[1] = false;
    poll();
  }
}

TEST(controls_input_callback_registration_and_dispatch) {
  ScopedInput input;
  zin::bind_mouse(3, kZoomLock);
  for (bool fixed : {false, true}) {
    zfix::set_all(fixed);
    EXPECT(zin::set_callback(kZoomLock, count_command) == static_cast<unsigned>(fixed));
    input.mouse.buttons[2] = 0x80;
    zin::poll(true);
    EXPECT(calls[kZoomLock] == static_cast<int>(fixed));
    EXPECT(zin::command(kZoomLock) == zin::kPressed);
    input.mouse.buttons[2] = 0;
    zin::poll(true);
    EXPECT(zin::command(kZoomLock) == zin::kReleased);
  }
  EXPECT(zin::set_callback(-1, count_command) == 0 && zin::set_callback(167, count_command) == 0);
  EXPECT(zin::set_callback(kNextWeapon, count_command) && zin::set_callback(kPreviousWeapon, count_command));
  input.weapon_edges = true;
  zin::poll(false);
  zin::state().map->enabled = 0;
  input.overlay = zin::kHeld;
  zin::poll(true);
  EXPECT(!input.saw_enabled && zin::command(kNextWeapon) == 0);
  zin::state().map->enabled = 1;
  zin::set_char_callback([](int32_t, int32_t, uintptr_t) {}, 0);
  zin::poll(true);
  EXPECT(input.saw_text && input.saw_enabled);
  EXPECT(calls[kNextWeapon] == 0 && calls[kPreviousWeapon] == 0);
  zin::set_char_callback(nullptr, 0);
  zin::poll(true);
  EXPECT(calls[kNextWeapon] == 1 && calls[kPreviousWeapon] == 1);
  EXPECT(zin::command(kNextWeapon) == zin::kHeld);
  EXPECT(zin::set_callback(kPreviousWeapon, nullptr) == 1);
  zin::poll(true);
  EXPECT(calls[kNextWeapon] == 2 && calls[kPreviousWeapon] == 1);

  // A callback can pop and destroy its own map mid-dispatch.
  zin::set_callback(kPreviousWeapon, count_command);
  zin::push_map(nullptr);
  zin::set_callback(kNextWeapon, [](int32_t) { zin::pop_map(); });
  zin::poll(true);
  EXPECT(zin::current_map() == zin::state().base.get() && calls[kPreviousWeapon] == 1);
}

TEST(controls_input_suppresses_only_constituent_sources) {
  ScopedInput input;
  zin::bind(kZoomLock, nullptr, zin::kCtrl | 0x11, 0x39, 1, 3);
  zin::set_callback(kZoomLock, count_command);
  input.suppress = true;
  input.mouse.buttons[2] = 0x80;
  input.events = {{0x1d, 0x80}, {0x11, 0x80}};
  zin::poll(true);
  EXPECT(zin::key_state(zin::kCtrl | 0x11) == zin::kPressed);
  EXPECT(calls[kZoomLock] == 0 && zin::command(kZoomLock) == 0);
  input.events = {{0x1d, 0}, {0x39, 0x80}};
  zin::poll(true);
  EXPECT(calls[kZoomLock] == 1 && zin::command(kZoomLock) == zin::kPressed);
  zin::state().joy.buttons[0] = 0x80;
  zin::poll(true);
  EXPECT(zin::command(kZoomLock) == (zin::kHeld | zin::kPressed));
}
