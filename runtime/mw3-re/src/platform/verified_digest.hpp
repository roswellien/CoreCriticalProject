// A full-file SHA-256 that is remembered across launches by file identity.
// Header-only so the derived-cache checks can test it without the core library.
#pragma once

#include "platform/sha256.hpp"
#include <cstdint>
#include <filesystem>
#include <stdexcept>
#include <string>

// The non-Windows header contract is also compiled by MSVC without POSIX headers.
#if defined(_WIN32) || __has_include(<sys/file.h>)
#include "platform/derived_cache.hpp"
#define MW3_VERIFIED_DIGEST_CACHE 1
#endif
#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#endif

namespace platform::verified_digest {
// Hashing every environment pack member was most of a launch: six campaign packs are about
// 29 GB, 90 s of SHA-256 on each start. As the old Python launcher's VerificationCache did, a
// member whose file identity, size and times match an earlier full hash reuses that digest
// from the derived cache (which is per executable and per write dir). Any rewrite of the file
// changes its write time and so hashes it again. With the cache off, every start hashes.
inline std::string sha256_file(const std::filesystem::path &path, std::uint64_t bytes) {
#if defined(MW3_VERIFIED_DIGEST_CACHE)
  // The derived cache when it is on; otherwise the digest-only cache, which the
  // benchmark configures (derived_cache.hpp, digest_cache), or nothing.
  auto &cache = platform::derived_cache::default_cache().is_enabled()
                    ? platform::derived_cache::default_cache()
                    : platform::derived_cache::digest_cache();
  std::string cache_key;
  if (cache.is_enabled()) {
    try {
      platform::derived_cache::KeyBuilder fingerprint("environment_member_sha256_v1");
      const auto spelling = path.u8string();
      fingerprint.update(spelling.data(), spelling.size());
      fingerprint.update_pod(bytes);
      const auto written = std::filesystem::last_write_time(path).time_since_epoch().count();
      fingerprint.update_pod(written);
#if defined(_WIN32)
      // Also the volume, the file's index on it and its creation time: a different file
      // copied into place with the same size and write time is still a new file.
      const HANDLE file = CreateFileW(path.c_str(), FILE_READ_ATTRIBUTES,
                                      FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                      nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
      if (file == INVALID_HANDLE_VALUE)
        throw std::runtime_error("no file identity");
      BY_HANDLE_FILE_INFORMATION information{};
      const bool identified = GetFileInformationByHandle(file, &information) != FALSE;
      CloseHandle(file);
      if (!identified)
        throw std::runtime_error("no file identity");
      fingerprint.update_pod(information.dwVolumeSerialNumber);
      fingerprint.update_pod(information.nFileIndexHigh);
      fingerprint.update_pod(information.nFileIndexLow);
      fingerprint.update_pod(information.ftCreationTime);
      fingerprint.update_pod(information.ftLastWriteTime);
#endif
      cache_key = fingerprint.hex();
      char digest[64];
      if (cache.read(cache_key, digest, sizeof digest))
        return std::string(digest, sizeof digest);
    } catch (const std::exception &) {
      cache_key.clear();  // No fingerprint: hash in full and remember nothing.
    }
  }
  auto digest = platform::integrity::sha256_file(path);
  if (!cache_key.empty() && digest.size() == 64)
    cache.write(cache_key, digest.data(), digest.size());
  return digest;
#else
  (void)bytes;
  return platform::integrity::sha256_file(path);
#endif
}
}  // namespace platform::verified_digest
