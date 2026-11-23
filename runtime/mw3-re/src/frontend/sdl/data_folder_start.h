#pragma once
// The usual folder and, through the pointer (mech3/data_folder.h), the player's
// data folder, as every program starts: mw3, mw3launcher, mw3import.
#include <SDL3/SDL.h>

#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

#include "gamez/zutil/zutl_path.h"
#include "mech3/data_folder.h"
#include "frontend/sdl/editor_context.h"
#include "upgrades/mods/marked_remove.h"

namespace sdlfe {

// A checked destination snapshot, not a B2 lease or race-safe confinement.
// Call lazily when opening the editor, never during ordinary closed startup.
inline EditorOwnedPaths editor_owned_paths(const std::string& write_root) {
  namespace fs = std::filesystem;
  if (write_root.empty() || write_root.find('\0') != std::string::npos)
    throw std::invalid_argument("editor: explicit write directory required");
  const fs::path selected(write_root);
  // Windows absolute() normalizes away '..'. Resolve only the root first,
  // retaining every supplied component for the ancestor link checks below.
  const fs::path absolute_root = selected.is_absolute() ? selected :
      (selected.has_root_path() ? fs::absolute(selected.root_path()) : fs::current_path()) / selected.relative_path();
  // Check the supplied spelling too: normalization must not hide a linked
  // ancestor before '..'. Standalone writeRoot == install remains supported.
  fs::path ancestor = absolute_root.root_path();
  for (const auto& part : absolute_root.relative_path()) {
    ancestor /= part;
    if (mech3::path_is_link(ancestor.string()) || !fs::is_directory(ancestor))
      throw std::runtime_error("editor: write directory ancestor is linked or unusable");
  }
  const fs::path root = absolute_root.lexically_normal();
  const fs::path child = root / "editor";
  const fs::path ini = child / "imgui.ini", log = child / "imgui_log.txt";
  if (mech3::path_is_link(child.string())) throw std::runtime_error("editor: metadata directory is linked");
  if (fs::exists(child) && !fs::is_directory(child))
    throw std::runtime_error("editor: metadata directory is not a directory");
  // Validate both leaves before creating anything; preserve existing data on
  // a bad second leaf. An append open tests access without truncation.
  for (const auto& leaf : {ini, log}) {
    if (mech3::path_is_link(leaf.string())) throw std::runtime_error("editor: metadata file is linked");
    if (fs::exists(leaf) && (!fs::is_regular_file(leaf) || fs::hard_link_count(leaf) != 1))
      throw std::runtime_error("editor: metadata file is not a unique regular file");
  }
  fs::create_directory(child);
  bool made_ini = false, made_log = false;
  try {
    for (const auto& leaf : {ini, log}) {
      const bool existed = fs::exists(leaf);
      if (!existed) (leaf == ini ? made_ini : made_log) = true;
      std::ofstream probe(leaf, std::ios::binary | std::ios::app);
      if (!probe) throw std::runtime_error("editor: metadata destination is not writable");
      probe.close();
      if (!probe) throw std::runtime_error("editor: metadata destination close failed");
    }
  } catch (...) {
    // Remove only newly created empty leaves, never preexisting files or a tree.
    std::error_code ignored;
    if (made_ini) fs::remove(ini, ignored);
    if (made_log) fs::remove(log, ignored);
    throw;
  }
  return {ini.generic_string(), log.generic_string()};
}

// The usual place; MW3_USUAL_FOLDER names another (checks).
inline std::string usual_folder(const char* game = "MechWarrior 3") {
  if (const char* env = std::getenv("MW3_USUAL_FOLDER")) return env;
  std::string dir;
  if (char* p = SDL_GetPrefPath("MicroProse", game)) dir = p, SDL_free(p);
  while (dir.size() > 1 && dir.back() == '/') dir.pop_back();
  return dir;
}

// Windows before 10 1903: a folder of the program's or the data with letters
// outside ASCII fails in odd ways, so it is said at the start (docs/program.md,
// Names on Windows).
inline bool names_usable(const std::string& data, bool ask) {
  if (zutl::narrow_paths_utf8()) return true;
  const char* base = SDL_GetBasePath();
  const std::string program = base ? base : "";
  auto plain = [](const std::string& s) {
    for (const char c : s)
      if (static_cast<unsigned char>(c) >= 0x80) return false;
    return true;
  };
  if (plain(program) && plain(data)) return true;
  const std::string text = "This version of Windows cannot use a folder whose name has letters outside plain English "
                           "(it needs Windows 10 version 1903 or later):\n\n" + (plain(program) ? data : program);
  std::fprintf(stderr, "mw3: %s\n", text.c_str());
  if (ask) SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "MechWarrior 3", text.c_str(), nullptr);
  return false;
}

// `dir` set to the folder to use. A pointer's folder that cannot be used is said
// and asked about again (a drive to connect), and never replaced by a fresh
// folder: false when the player quits, or at once when `ask` is false.
inline bool data_folder_at_start(std::string* dir, bool ask, bool* pointer = nullptr, const char* game = "MechWarrior 3") {
  const std::string usual = usual_folder(game);
  for (;;) {
    const mech3::data_folder::Resolved r = mech3::data_folder::resolve(usual);
    if (pointer) *pointer = r.pointer;
    if (r.error.empty()) {
      *dir = r.dir;
      return names_usable(r.dir, ask);
    }
    std::fprintf(stderr, "mw3: %s\n", r.error.c_str());
    if (!ask) return false;
    const SDL_MessageBoxButtonData buttons[] = {{SDL_MESSAGEBOX_BUTTON_RETURNKEY_DEFAULT, 1, "Try again"},
                                                {SDL_MESSAGEBOX_BUTTON_ESCAPEKEY_DEFAULT, 0, "Quit"}};
    SDL_MessageBoxData box{};
    box.flags = SDL_MESSAGEBOX_ERROR, box.title = "MechWarrior 3", box.message = r.error.c_str();
    box.numbuttons = 2, box.buttons = buttons;
    int chose = 0;
    if (!SDL_ShowMessageBox(&box, &chose) || chose != 1) return false;
  }
}

}  // namespace sdlfe
