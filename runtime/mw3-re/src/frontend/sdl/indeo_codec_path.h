#pragma once

#include <cctype>
#include <filesystem>
#include <string>

namespace sdlfe {

// The launcher supplies this path only after checking the original DLL's pinned identity.
// Standalone starts retain the install-root lookup used before the launcher integration.
inline std::string indeo_codec_path(const std::string& install, const std::string& preferred) {
  std::error_code ec;
  if (!preferred.empty() && std::filesystem::is_regular_file(preferred, ec)) return preferred;
  ec.clear();
  for (const auto& entry : std::filesystem::directory_iterator(install, ec)) {
    std::string name = entry.path().filename().string();
    for (char& character : name)
      character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    if (name == "ir50_32.dll" && entry.is_regular_file(ec)) return entry.path().string();
    ec.clear();
  }
  return {};
}

}  // namespace sdlfe
