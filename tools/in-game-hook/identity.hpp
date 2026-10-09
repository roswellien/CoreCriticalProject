#pragma once
#include <windows.h>
#include <bcrypt.h>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::hook {
constexpr auto game_sha = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf";
constexpr auto leaf_sha = "560c17c210dd7fedd7de601f42570c2a0473fa71962c13cfa85a005509a77c65";
constexpr std::uintptr_t guest_entry = 0x409ed0;
constexpr std::size_t leaf_size = 22;
constexpr std::size_t leaf_offset = 0x92d0;
constexpr std::uint32_t arithmetic_mask = 0x8d5;
constexpr std::uint32_t observed_mask = 0xcd5;

inline std::string sha256(const void *data, std::size_t size) {
    static_assert(sizeof(std::size_t) == sizeof(ULONG), "Hash bridge is Win32 only");
    std::array<UCHAR, 32> hash{};
    BCRYPT_ALG_HANDLE algorithm{};
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0)
        throw std::runtime_error("SHA-256 provider unavailable");
    const auto result = BCryptHash(algorithm, nullptr, 0,
        static_cast<PUCHAR>(const_cast<void *>(data)), static_cast<ULONG>(size), hash.data(),
        static_cast<ULONG>(hash.size()));
    BCryptCloseAlgorithmProvider(algorithm, 0);
    if (result < 0) throw std::runtime_error("SHA-256 failed");
    constexpr char hex[] = "0123456789abcdef";
    std::string text;
    for (auto value : hash) {
        text.push_back(hex[value >> 4]);
        text.push_back(hex[value & 15]);
    }
    return text;
}
inline std::vector<std::uint8_t> admitted_image(const std::wstring &path) {
    std::ifstream file(std::filesystem::path(path), std::ios::binary | std::ios::ate);
    if (!file || file.tellg() != 2384384) throw std::runtime_error("Wrong game size or inaccessible file");
    file.seekg(0);
    std::vector<std::uint8_t> bytes(2384384);
    if (!file.read(reinterpret_cast<char *>(bytes.data()), static_cast<std::streamsize>(bytes.size())) ||
        sha256(bytes.data(), bytes.size()) != game_sha)
        throw std::runtime_error("Unsupported game hash");
    if (sha256(bytes.data() + leaf_offset, leaf_size) != leaf_sha)
        throw std::runtime_error("Unsupported leaf hash");
    return bytes;
}
inline std::wstring environment(const wchar_t *name) {
    std::array<wchar_t, 32768> buffer{};
    const auto count = GetEnvironmentVariableW(name, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (!count || count >= buffer.size()) throw std::runtime_error("Required research environment missing");
    return std::wstring(buffer.data(), count);
}
} // namespace mw34::hook
