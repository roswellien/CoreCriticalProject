// Project-authored pipeline-state recipe. Stores configuration numbers only,
// never driver binaries, shaders, original data or generated game code.
#pragma once
#include <windows.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>

namespace mw34::pipeline_warmup {
inline constexpr std::size_t capacity = 64;
inline bool valid(std::uint64_t key) {
    if (key >> 60) return false;
    const auto byte = [key](unsigned shift) { return unsigned((key >> shift) & 255); };
    const unsigned flags = unsigned(key >> 56);
    return byte(0) <= 1 && byte(8) <= 11 && byte(16) <= 11 && byte(24) <= 1 &&
           byte(32) >= 1 && byte(32) <= 8 && byte(40) <= 1 &&
           byte(48) >= 1 && byte(48) <= 3 && (!(flags & 4) || (flags & 2));
}
inline bool parse(std::istream &input, std::set<std::uint64_t> &keys) {
    std::string magic;
    if (!std::getline(input, magic) || magic != "MW34PIPE1") return false;
    std::set<std::uint64_t> parsed;
    std::string line;
    while (std::getline(input, line)) {
        if (line.empty() || line.size() > 16) return false;
        std::istringstream record(line);
        std::uint64_t key{};
        if (!(record >> std::hex >> key) || !record.eof() || !valid(key) ||
            !parsed.insert(key).second || parsed.size() > capacity) return false;
    }
    if (!input.eof()) return false;
    keys = std::move(parsed);
    return true;
}

class Recipe {
    std::filesystem::path path;
    std::set<std::uint64_t> keys;
    bool dirty{};
public:
    const std::set<std::uint64_t> &states() const { return keys; }
    void load(const char *renderer) {
        const char *directory = std::getenv("MW34_PIPELINE_WARMUP_DIR");
        if (!directory || !*directory) return;
        const char *enabled = std::getenv("MW34_PIPELINE_WARMUP");
        if (enabled && std::strcmp(enabled, "0") && std::strcmp(enabled, "1"))
            throw std::runtime_error("MW34_PIPELINE_WARMUP must be 0 or 1");
        if (enabled && !std::strcmp(enabled, "0")) return;
        path = std::filesystem::path(directory) / (std::string(renderer) + ".keys");
        try {
            if (!std::filesystem::exists(path)) return;
            if (!std::filesystem::is_regular_file(path) || std::filesystem::is_symlink(path) ||
                std::filesystem::file_size(path) > 4096) {
                std::fprintf(stderr, "Pipeline warmup: ignoring invalid optional recipe\n");
                return;
            }
            std::ifstream input(path);
            if (!parse(input, keys))
                std::fprintf(stderr, "Pipeline warmup: ignoring invalid optional recipe\n");
        } catch (const std::exception &) {
            std::fprintf(stderr, "Pipeline warmup: optional recipe unavailable\n");
        }
    }
    void record(std::uint64_t key) {
        if (path.empty() || !valid(key) || keys.size() >= capacity || keys.contains(key)) return;
        keys.insert(key);
        dirty = true;
    }
    void save() noexcept {
        if (path.empty() || !dirty) return;
        // No filesystem writes in the frame loop. Publish only after normal shutdown.
        std::filesystem::path temporary;
        try {
            std::filesystem::create_directories(path.parent_path());
            temporary = path;
            temporary += "." + std::to_string(GetCurrentProcessId()) + "." +
                         std::to_string(GetTickCount64()) + ".tmp";
            std::ostringstream text;
            text << "MW34PIPE1\n";
            for (auto key : keys) text << std::hex << key << '\n';
            const auto bytes = text.str();
            HANDLE file = CreateFileW(temporary.c_str(), GENERIC_WRITE, 0, nullptr,
                                      CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
            if (file == INVALID_HANDLE_VALUE) throw std::runtime_error("recipe create");
            DWORD written{};
            const bool ok = WriteFile(file, bytes.data(), DWORD(bytes.size()), &written, nullptr) &&
                            written == bytes.size() && FlushFileBuffers(file);
            CloseHandle(file);
            if (!ok || !MoveFileExW(temporary.c_str(), path.c_str(),
                                   MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH))
                throw std::runtime_error("recipe publish");
            dirty = false;
        } catch (...) {
            std::fprintf(stderr, "Pipeline warmup: could not save optional recipe\n");
            if (!temporary.empty()) { std::error_code ignored; std::filesystem::remove(temporary, ignored); }
        }
    }
};
} // namespace mw34::pipeline_warmup
