// Ours, not original code: a helper program (mw3import, the Video for Windows
// helper) started with its stdin and stdout piped to us. On Windows, when mw3
// has no console of its own (the package build is a GUI program, docs/
// windows.md), a console child would open a console window beside the game;
// SDL starts it without one only as a "background" process (CREATE_NO_WINDOW),
// whose exit code then always reads 0 (callers judge the result otherwise).
#pragma once

#include <string>

#include <SDL3/SDL.h>

namespace sdlfe {

SDL_Process* start_child(const char* const* args);

// The launcher's signal that the game is on screen (docs/launcher.md, The
// two programs): mw3 --ready-file PATH writes PATH once its first frame is
// shown, and the launcher hides then, so there is no moment with neither.
void set_ready_file(const std::string& path);
void mark_menu_ready();  // a presented main-menu frame, distinct from the first frame
void mark_ready();  // the first call writes it; later ones do nothing
// What the game is doing before its first frame, for the launcher's status
// line (PATH.status beside the ready file); "" removes it. Nothing without
// --ready-file.
void set_ready_status(const std::string& text);

// The process's resident memory in KB (the soak test's lines); 0 where unknown.
size_t resident_kb();

}  // namespace sdlfe
