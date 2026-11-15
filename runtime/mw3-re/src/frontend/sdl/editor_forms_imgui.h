// Ours, not original code: Dear ImGui for the editor's dialogs.
// Extracted form/widget view and event predicates without GPU/renderer backend.
#pragma once

#include <string>

#include <SDL3/SDL.h>

namespace mech3 {
struct EditorForm;
}

namespace sdlfe {

// Whether an event goes on to zInput while the editor's ImGui is up: a mouse
// event when ImGui does not want the mouse, a key or text event when it wants
// neither the keyboard nor text. Everything else (the window's, the pad's)
// goes on as before.
bool editor_event_to_game(const SDL_Event& e, bool want_mouse, bool want_keyboard, bool want_text);

// Every form shown (upgrades/editor/form.h) as an ImGui window, or a modal
// popup; EditorUi's default `draw`.
void draw_editor_forms();
// The tests: where the last frame drew a form's field or button (window pixels).
bool editor_item_rect(const mech3::EditorForm* f, const std::string& label, float r[4]);

}  // namespace sdlfe
