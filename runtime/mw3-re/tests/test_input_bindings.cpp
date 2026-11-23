#include "check.h"
#include "frontend/sdl/sdl_input.h"
#include "platform/sha256.hpp"

#include <filesystem>
#include <fstream>
#include <iterator>
#include <string_view>

namespace {
using platform::Input;
using sdlfe::SdlInput;
namespace fs = std::filesystem;

std::string fixture(const char* name, const char* contents) {
  const auto path = fs::path(MW3_TEST_TMP) / name;
  std::ofstream file(path, std::ios::binary);
  file << contents;
  EXPECT(file.good());
  return path.generic_string();
}

void acquire(SdlInput& input, Input::Device device) {
  EXPECT(input.open(device));
  EXPECT(input.acquire(device) == 0);
}

void button(SdlInput& input, Uint8 id, bool down) {
  SDL_Event event{};
  event.type = down ? SDL_EVENT_MOUSE_BUTTON_DOWN : SDL_EVENT_MOUSE_BUTTON_UP;
  event.button.button = id;
  input.on_event(event);
}

void key(SdlInput& input, SDL_Scancode scan, bool down) {
  SDL_Event event{};
  event.type = down ? SDL_EVENT_KEY_DOWN : SDL_EVENT_KEY_UP;
  event.key.scancode = scan;
  input.on_event(event);
}

void wheel(SdlInput& input, float y) {
  SDL_Event event{};
  event.type = SDL_EVENT_MOUSE_WHEEL;
  event.wheel.y = y;
  input.on_event(event);
}

platform::MouseState poll(SdlInput& input, bool text = false, bool commands = true) {
  input.begin_poll(text, commands);
  platform::MouseState mouse{};
  EXPECT(input.mouse_state(&mouse) == 0);
  return mouse;
}
}  // namespace

TEST(extended_sdl_buttons_snapshot_and_legacy_latches) {
  SdlInput input;
  size_t count = 0;
  EXPECT(input.set_input_bindings(fixture("extended-buttons.txt",
      "CC_MW3_INPUT_V1\nMOUSE 61 4\nMOUSE 62 5\nCOMBO 63 1 2 K:11 M:5\n"), &count));
  EXPECT(count == 3 && input.command_has_extended_binding(62) && !input.command_has_extended_binding(0));
  acquire(input, Input::kMouse);
  acquire(input, Input::kKeyboard);
  button(input, SDL_BUTTON_LEFT, true);
  button(input, SDL_BUTTON_LEFT, false);
  button(input, SDL_BUTTON_X1, true);
  button(input, SDL_BUTTON_X1, false);
  button(input, SDL_BUTTON_X2, true);
  button(input, SDL_BUTTON_X2, false);
  const auto mouse = poll(input);
  EXPECT(mouse.buttons[0] == 0x80 && mouse.buttons[3] == 0x80 && input.mouse_buttons == 0);
  EXPECT(input.mouse_input_down(1) && input.mouse_input_down(4) && input.mouse_input_down(5));
  EXPECT(input.command_state(61) == zin::kPressed && input.extended_command_pressed(61));
  EXPECT(!input.joystick() && input.command_state(62) == zin::kPressed && input.extended_command_pressed(62));
  const auto next = poll(input);
  EXPECT(next.buttons[0] == 0 && next.buttons[3] == 0);
  EXPECT(!input.mouse_input_down(5) && input.command_state(62) == zin::kReleased);

  // A begin_poll without a legacy device read still consumes X2's latch.
  button(input, SDL_BUTTON_X2, true);
  button(input, SDL_BUTTON_X2, false);
  input.begin_poll(false, true);
  EXPECT(input.mouse_input_down(5));
  input.begin_poll(false, true);
  EXPECT(!input.mouse_input_down(5));
  button(input, SDL_BUTTON_X2, true);
  button(input, SDL_BUTTON_X2, false);
  platform::MouseState direct{};
  EXPECT(input.mouse_state(&direct) == 0);
  EXPECT(poll(input).buttons[3] == 0 && !input.mouse_input_down(5));

  key(input, SDL_SCANCODE_W, true);
  button(input, SDL_BUTTON_X2, true);
  poll(input);
  EXPECT(input.mouse_input_down(5) && input.mouse_suppressed(5) && input.key_suppressed(0x11));
  EXPECT(input.extended_command_pressed(63) && input.command_state(62) == 0);
  key(input, SDL_SCANCODE_W, false);
  poll(input);
  EXPECT(input.mouse_input_down(5) && !input.mouse_suppressed(5) && !input.key_suppressed(0x11));
  EXPECT(input.command_state(62) == zin::kPressed && !input.extended_command_pressed(62));
  input.unacquire(Input::kMouse);
  input.begin_poll(false, true);
  EXPECT(!input.mouse_input_down(5) && input.command_state(62) == 0);
}

TEST(extended_sdl_wheel_routes_at_poll_boundary) {
  SdlInput input;
  input.set_input_bindings(fixture("extended-wheel.txt", "CC_MW3_INPUT_V1\nMOUSE 61 6\n"));
  bool mission = false;
  input.in_mission = [&] { return mission; };
  acquire(input, Input::kMouse);
  poll(input, false, false);
  mission = true;
  wheel(input, 0.5f);
  wheel(input, -0.5f);
  EXPECT(poll(input).z == -60 && !input.mouse_input_down(6));
  wheel(input, 0.5f);
  EXPECT(poll(input).z == 0 && input.extended_command_pressed(61));
  wheel(input, 1.25f);  // first event for the new text-entry poll
  EXPECT(poll(input, true).z == 150 && !input.mouse_input_down(6) && input.command_state(61) == 0);
  wheel(input, 0.75f);  // first event back in commands
  EXPECT(poll(input).z == 0 && !input.mouse_input_down(6));
  wheel(input, 0.25f);
  EXPECT(poll(input).z == 0 && input.mouse_input_down(6));
  mission = false;
  wheel(input, 0.5f);
  EXPECT(poll(input, false, false).z == 60 && !input.extended_command_pressed(61));
  wheel(input, 12.0f);
  wheel(input, -1.0f);
  for (int i = 0; i < 9; ++i) {
    const bool pulse = i < 8 && i % 2 == 0;
    EXPECT(poll(input).z == (i == 0 ? -120 : 0));
    EXPECT(input.mouse_input_down(6) == pulse && input.extended_command_pressed(61) == pulse);
  }

  // A headlight-only binding routes the other direction independently.
  input.set_headlight_wheel(2);
  wheel(input, 0.5f);
  wheel(input, -0.75f);
  EXPECT(poll(input).z == 0 && !input.mouse_input_down(6) && !input.mouse_input_down(7));
  wheel(input, -0.25f);
  EXPECT(poll(input).z == 0 && !input.mouse_input_down(6) && input.mouse_input_down(7));
  wheel(input, 0.5f);
  EXPECT(poll(input).z == 0 && input.mouse_input_down(6) && !input.mouse_input_down(7));

  input.set_headlight_wheel(0);
  input.set_input_bindings(fixture("extended-wheel-chord.txt", "CC_MW3_INPUT_V1\nCOMBO 62 1 2 K:11 M:7\n"));
  acquire(input, Input::kKeyboard);
  key(input, SDL_SCANCODE_W, true);
  wheel(input, -1.0f);
  EXPECT(poll(input).z == 0 && input.mouse_suppressed(7) && input.extended_command_pressed(62));
}

TEST(extended_sdl_focus_loading_mission_and_mute_clear_input) {
  SdlInput input;
  input.set_input_bindings(fixture("extended-reset.txt",
      "CC_MW3_INPUT_V1\nMOUSE 61 6\nCOMBO 62 1 2 K:11 M:5\n"));
  bool mission = false;
  input.in_mission = [&] { return mission; };
  input.windowed = [] { return true; };
  acquire(input, Input::kMouse);
  acquire(input, Input::kKeyboard);
  auto prime = [&] {
    key(input, SDL_SCANCODE_W, true);
    button(input, SDL_BUTTON_X2, true);
    wheel(input, 2.5f);
    EXPECT(poll(input).z == 0);
    EXPECT(input.mouse_suppressed(5) && input.key_suppressed(0x11) && input.mouse_input_down(6));
    wheel(input, 1.0f);  // pending event plus queued and fractional state
  };
  auto cleared = [&] {
    for (int i = 0; i < 3; ++i) {
      EXPECT(poll(input).z == 0);
      EXPECT(!input.mouse_input_down(5) && !input.mouse_input_down(6));
      EXPECT(!input.mouse_suppressed(5) && !input.key_suppressed(0x11));
      EXPECT(input.command_state(61) == 0 && input.command_state(62) == 0);
    }
    wheel(input, 0.5f);
    EXPECT(poll(input).z == 0 && !input.mouse_input_down(6));
    input.discard_loading_input();
  };

  prime();
  SDL_Event focus{};
  focus.type = SDL_EVENT_WINDOW_FOCUS_LOST;
  input.on_event(focus);
  EXPECT(!input.mouse_input_down(6) && !input.key_suppressed(0x11));
  focus.type = SDL_EVENT_WINDOW_FOCUS_GAINED;
  input.on_event(focus);
  cleared();

  prime();
  input.discard_loading_input();
  cleared();

  prime();
  mission = true;
  EXPECT(poll(input).z == 0 && !input.mouse_input_down(5));
  button(input, SDL_BUTTON_X2, true);  // stale down while the transition press is still held
  EXPECT(poll(input).z == 0 && !input.mouse_input_down(5));
  button(input, SDL_BUTTON_X2, false);
  cleared();

  prime();
  mission = false;
  cleared();
  mission = true;
  poll(input);  // enter before priming the release chord
  prime();
  key(input, SDL_SCANCODE_LCTRL, true);
  key(input, SDL_SCANCODE_LALT, true);
  key(input, SDL_SCANCODE_LALT, false);
  key(input, SDL_SCANCODE_LCTRL, false);
  EXPECT(input.released());
  EXPECT(poll(input).z == 0 && !input.mouse_input_down(5) && !input.mouse_input_down(6));
  button(input, SDL_BUTTON_X2, false);
  button(input, SDL_BUTTON_X2, true);  // recapture click is swallowed
  EXPECT(!input.released());
  cleared();
}

TEST(extended_sdl_merges_virtual_controller_and_mouse_actions) {
  EXPECT(SDL_InitSubSystem(SDL_INIT_GAMEPAD));
  SDL_VirtualJoystickDesc desc;
  SDL_INIT_INTERFACE(&desc);
  desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
  desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
  desc.nbuttons = SDL_GAMEPAD_BUTTON_COUNT;
  desc.name = "mw3 extended input test pad";
  const auto id = SDL_AttachVirtualJoystick(&desc);
  SDL_Gamepad* pad = SDL_OpenGamepad(id);
  EXPECT(pad != nullptr);
  if (!pad) {
    if (id) SDL_DetachVirtualJoystick(id);
    SDL_QuitSubSystem(SDL_INIT_GAMEPAD);
    return;
  }
  std::string identity;
  constexpr char hex[] = "0123456789ABCDEF";
  for (uint8_t byte : SDL_GetGamepadGUIDForID(id).data) {
    identity.push_back(hex[byte >> 4]);
    identity.push_back(hex[byte & 15]);
  }
  const char* serial = SDL_GetGamepadSerial(pad);
  const char* path = SDL_GetGamepadPath(pad);
  const std::string serial_text = serial ? serial : "";
  const std::string path_text = path ? path : "";
  identity += ":" + (serial_text.empty() ? path_text : serial_text);
  if (serial_text.empty() && path_text.empty()) identity += ":session:" + std::to_string(id);
  platform::integrity::Sha256 digest;
  digest.update(identity.data(), identity.size());
  const auto profile = fs::path(MW3_TEST_TMP) / "extended-controller.txt";
  {
    std::ofstream file(profile);
    file << "CC_MW3_CONTROLLER_V1\n" << digest.hex() << '\n';
    for (int i = 0; i < 6; ++i)
      file << (i < 4 ? "-32768" : "0") << " 0 32767 0 1 0\n";
    for (int i = 0; i < 26; ++i) file << (i == SDL_GAMEPAD_BUTTON_SOUTH ? 61 : 0) << ' ';
    file << "\n0 0\n1 0 2 3\n-1 1 1 1\n0.25\n";
    EXPECT(file.good());
  }
  SdlInput input;
  input.joystick_disabled = true;  // require the virtual profile's identity to match
  input.controller_profile_path = profile.generic_string();
  input.set_input_bindings(fixture("extended-controller-mouse.txt", "CC_MW3_INPUT_V1\nMOUSE 61 5\n"));
  acquire(input, Input::kJoystick);
  acquire(input, Input::kMouse);
  platform::JoyState joy{};
  EXPECT(input.joystick_state(&joy) == 0);  // neutral sample arms the profile
  EXPECT(SDL_SetJoystickVirtualButton(SDL_GetGamepadJoystick(pad), SDL_GAMEPAD_BUTTON_SOUTH, true));
  EXPECT(input.joystick_state(&joy) == 0 && input.command_state(61) == zin::kPressed);
  button(input, SDL_BUTTON_X2, true);
  poll(input);
  EXPECT(input.joystick_state(&joy) == 0 && input.command_state(61) == (zin::kHeld | zin::kPressed));
  EXPECT(poll(input, true).z == 0 && input.command_state(61) == zin::kHeld);
  input.close(Input::kJoystick);
  poll(input);
  EXPECT(input.command_state(61) == zin::kPressed);
  SDL_CloseGamepad(pad);
  SDL_DetachVirtualJoystick(id);
  SDL_QuitSubSystem(SDL_INIT_GAMEPAD);
}

TEST(extended_sdl_input_cli_rejects_invalid_arguments_and_files) {
  const auto root = fs::path(MW3_TEST_TMP) / "input CLI";
  fs::create_directories(root / "zbd");
  std::ofstream(root / "zbd" / "reader.zbd").put('\0');  // startup only checks for presence
  const auto install = root.generic_string();
  const auto invalid = fixture("extended-invalid.txt", "CC_MW3_INPUT_V1\nMOUSE 61 8\n");
  const auto missing = (root / "missing.txt").generic_string();
  auto run = [&](std::initializer_list<const char*> operands, int expected, std::string_view message) {
    const auto write = install + "/write-" + std::to_string(operands.size()) + "-" +
                       std::to_string(expected);
    fs::create_directories(write);
    std::vector<const char*> argv{MW3_BIN, "--hidden", "--nosound", "--no-launcher", "--frames", "1", "--install",
                                  install.c_str(), "--write-dir", write.c_str(), "--cc-input"};
    argv.insert(argv.end(), operands);
    argv.push_back(nullptr);
    const auto props = SDL_CreateProperties();
    SDL_SetPointerProperty(props, SDL_PROP_PROCESS_CREATE_ARGS_POINTER, argv.data());
    SDL_SetNumberProperty(props, SDL_PROP_PROCESS_CREATE_STDOUT_NUMBER, SDL_PROCESS_STDIO_APP);
    SDL_SetBooleanProperty(props, SDL_PROP_PROCESS_CREATE_STDERR_TO_STDOUT_BOOLEAN, true);
    SDL_Process* child = SDL_CreateProcessWithProperties(props);
    SDL_DestroyProperties(props);
    EXPECT(child != nullptr);
    if (!child) return;
    int status = -1;
    size_t size = 0;
    char* bytes = static_cast<char*>(SDL_ReadProcess(child, &size, &status));
    std::string output = bytes ? std::string(bytes, size) : std::string{};
    SDL_free(bytes);
    SDL_DestroyProcess(child);
    // With no console on Windows the program writes its startup errors to mw3.log.
    std::ifstream log(fs::path(write) / "mw3.log");
    output.append(std::istreambuf_iterator<char>(log), std::istreambuf_iterator<char>());
    std::printf("  --cc-input child exit %d (expected %d): %.*s\n",
                status, expected, static_cast<int>(message.size()), message.data());
    if (status != expected || output.find(message) == output.npos) std::printf("%s\n", output.c_str());
    EXPECT(status == expected && output.find(message) != output.npos);
  };
  run({}, 2, "--cc-input requires a file path");
  run({""}, 2, "--cc-input requires a file path");
  run({"--other-flag"}, 2, "--cc-input requires a file path");
  run({missing.c_str()}, 1, "Cannot open MW3 input bindings:");
  run({invalid.c_str()}, 1, "Invalid MW3 input number: 8");
}
