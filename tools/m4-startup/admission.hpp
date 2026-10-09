#pragma once

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <limits>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::m4 {

inline constexpr std::size_t admitted_image_size = 2384384;
inline constexpr const char *admitted_image_hash =
    "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf";

inline void require_admission(bool condition, const char *reason) {
    if (!condition) {
        throw std::runtime_error(reason);
    }
}

// Same Windows SHA256 provider used in the accepted earlier workers. The hash
// handle is destroyed before its caller-owned object buffer and provider.
inline std::string sha256(std::span<const std::byte> bytes) {
    struct Algorithm {
        BCRYPT_ALG_HANDLE value{};
        ~Algorithm() {
            if (value) {
                BCryptCloseAlgorithmProvider(value, 0);
            }
        }
    } algorithm;
    require_admission(BCryptOpenAlgorithmProvider(&algorithm.value, BCRYPT_SHA256_ALGORITHM,
                                                nullptr, 0) >= 0,
                      "SHA256 provider failed");
    DWORD object_size{}, returned{};
    require_admission(BCryptGetProperty(algorithm.value, BCRYPT_OBJECT_LENGTH,
                                       reinterpret_cast<PUCHAR>(&object_size), sizeof(object_size),
                                       &returned, 0) >= 0 && returned == sizeof(object_size),
                      "SHA256 property failed");
    std::vector<unsigned char> object(object_size);
    std::array<unsigned char, 32> digest{};
    struct Hash {
        BCRYPT_HASH_HANDLE value{};
        ~Hash() {
            if (value) {
                BCryptDestroyHash(value);
            }
        }
    } hash;
    require_admission(BCryptCreateHash(algorithm.value, &hash.value, object.data(), object_size,
                                      nullptr, 0, 0) >= 0,
                      "SHA256 create failed");
    require_admission(bytes.size() <= std::numeric_limits<ULONG>::max(),
                      "SHA256 input exceeds bounded provider size");
    if (!bytes.empty()) {
        auto *input = reinterpret_cast<unsigned char *>(const_cast<std::byte *>(bytes.data()));
        require_admission(BCryptHashData(hash.value, input, static_cast<ULONG>(bytes.size()), 0) >= 0,
                          "SHA256 input failed");
    }
    require_admission(BCryptFinishHash(hash.value, digest.data(),
                                      static_cast<ULONG>(digest.size()), 0) >= 0,
                      "SHA256 finish failed");
    constexpr char hex[] = "0123456789abcdef";
    std::string result;
    result.reserve(64);
    for (const auto byte : digest) {
        result += hex[byte >> 4];
        result += hex[byte & 15];
    }
    return result;
}

inline std::vector<std::byte> read_image(const std::filesystem::path &path) {
    std::ifstream stream(path, std::ios::binary | std::ios::ate);
    require_admission(bool(stream), "Missing M4 image input");
    const auto end = stream.tellg();
    require_admission(end >= 0 && static_cast<std::uint64_t>(end) <= 64U * 1024U * 1024U,
                      "M4 input exceeds bounded file size");
    std::vector<std::byte> bytes(static_cast<std::size_t>(end));
    stream.seekg(0);
    require_admission(bool(stream), "M4 input seek failed");
    if (!bytes.empty()) {
        require_admission(bool(stream.read(reinterpret_cast<char *>(bytes.data()),
                                           static_cast<std::streamsize>(bytes.size()))),
                          "M4 input changed or could not be read");
    }
    require_admission(stream.peek() == std::char_traits<char>::eof(),
                      "M4 input grew during bounded read");
    return bytes;
}

inline void admit_image(std::span<const std::byte> bytes) {
    require_admission(bytes.size() == admitted_image_size, "Wrong M4 image size");
    require_admission(sha256(bytes) == admitted_image_hash, "Wrong M4 image identity");
}

inline unsigned admission_controls() {
    unsigned checks = 0;
    require_admission(sha256({}) ==
                          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                      "SHA256 empty known-answer mismatch");
    ++checks;
    const std::array<std::byte, 3> abc{std::byte{'a'}, std::byte{'b'}, std::byte{'c'}};
    require_admission(sha256(abc) ==
                          "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                      "SHA256 abc known-answer mismatch");
    ++checks;
    const std::vector<std::byte> million_a(1000000, std::byte{'a'});
    require_admission(sha256(million_a) ==
                          "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0",
                      "SHA256 multi-block known-answer mismatch");
    ++checks;
    auto reject = [&](std::span<const std::byte> bytes, const char *expected) {
        try {
            admit_image(bytes);
        } catch (const std::exception &error) {
            require_admission(std::string(error.what()) == expected,
                              "Wrong image admission rejection cause");
            ++checks;
            return;
        }
        throw std::runtime_error("Image admission accepted unsupported input");
    };
    reject({}, "Wrong M4 image size");
    reject(std::vector<std::byte>(admitted_image_size), "Wrong M4 image identity");
    return checks;
}

} // namespace mw34::m4
