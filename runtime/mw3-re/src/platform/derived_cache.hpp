// Derived result cache for recomputed or format-converted game assets.
// C++17 header-only library under namespace platform::derived_cache.
#ifndef PLATFORM_DERIVED_CACHE_HPP
#define PLATFORM_DERIVED_CACHE_HPP

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
// Win32's DrawState alias must not rename the renderer's platform::DrawState.
#ifdef DrawState
#undef DrawState
#endif
#ifdef near
#undef near
#endif
#else
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#endif

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <memory>
#include <mutex>
#include <string>
#include <string_view>
#include <system_error>
#include <type_traits>
#include <vector>

#include "platform/sha256.hpp"

namespace platform::derived_cache {

// Maximum size of any single cached entry payload: 256 MiB.
inline constexpr uint64_t kMaxEntryPayloadBytes = 256ULL * 1024ULL * 1024ULL;

// Default total cache size limit: 2 GiB.
inline constexpr uint64_t kDefaultCapacityBytes = 2048ULL * 1024ULL * 1024ULL;
// Leave room for the lock, staging directory and unrelated files below the
// scan guard; many tiny entries must evict rather than stop all future writes.
inline constexpr std::size_t kMaximumCacheEntries = 9000;

// Binary cache entry magic and version tag.
inline constexpr char kEntryMagic[8] = {'M', 'W', '3', 'D', 'C', 'H', '1', '\0'};
inline constexpr uint32_t kEntryVersion = 1;

#pragma pack(push, 1)
// On-disk entry header placed at the beginning of each key.bin file.
// All integer sizes and hashes are verified before payload allocation.
struct EntryHeader {
  char magic[8];            // "MW3DCH1\0"
  uint32_t version;         // kEntryVersion
  char key[64];             // 64 lowercase hex characters
  uint64_t payload_size;    // Size of following payload in bytes
  char payload_sha256[64];  // SHA-256 digest of payload in lowercase hex
};
#pragma pack(pop)
static_assert(sizeof(EntryHeader) == 8 + 4 + 64 + 8 + 64, "EntryHeader must be 148 bytes");

// Validates that a key consists strictly of 64 lowercase hexadecimal digits.
// Rejects path traversal attempts, uppercase letters, and irregular lengths.
inline bool is_valid_key(std::string_view key) noexcept {
  if (key.size() != 64) {
    return false;
  }
  for (char c : key) {
    const bool is_digit = (c >= '0' && c <= '9');
    const bool is_lower_hex = (c >= 'a' && c <= 'f');
    if (!is_digit && !is_lower_hex) {
      return false;
    }
  }
  return true;
}

// Initialization precedes parallel decoding; atomic publication also keeps a
// reader's identity stable if a future frontend reconfigures between sessions.
inline std::shared_ptr<const std::string>& producer_identity_holder() {
  static std::shared_ptr<const std::string> identity = std::make_shared<const std::string>();
  return identity;
}

inline void configure_producer_identity(std::string identity) {
  std::atomic_store(&producer_identity_holder(),
      std::make_shared<const std::string>(std::move(identity)));
}

// Streaming key builder that frames domain and source without huge intermediate buffers.
class KeyBuilder {
public:
  explicit KeyBuilder(std::string_view domain) {
    sha_.update(&kEntryVersion, sizeof(kEntryVersion));
    const auto producer = std::atomic_load(&producer_identity_holder());
    const uint64_t producer_length = producer->size();
    sha_.update(&producer_length, sizeof(producer_length));
    sha_.update(producer->data(), producer->size());
    const uint64_t domain_length = static_cast<uint64_t>(domain.size());
    sha_.update(&domain_length, sizeof(domain_length));
    if (!domain.empty()) {
      sha_.update(domain.data(), domain.size());
    }
  }

  void update(const void* data, std::size_t size) {
    if (data != nullptr && size > 0) {
      sha_.update(data, size);
    }
  }

  template <typename T>
  void update_pod(const T& val) {
    static_assert(std::is_standard_layout_v<T>, "update_pod requires standard layout type");
    sha_.update(&val, sizeof(T));
  }

  // Returns the 64-character lowercase hex digest.
  std::string hex() const {
    return sha_.hex();
  }

private:
  platform::integrity::Sha256 sha_;
};

// Computes SHA256 over unambiguously length-framed domain plus full source bytes.
inline std::string key(const void* source, std::size_t size, std::string_view domain) {
  KeyBuilder builder(domain);
  const uint64_t source_length = static_cast<uint64_t>(size);
  builder.update(&source_length, sizeof(source_length));
  if (source != nullptr && size > 0) {
    builder.update(source, size);
  }
  return builder.hex();
}

// Current process ID helper for unique staging file generation.
inline uint32_t current_process_id() noexcept {
#if defined(_WIN32)
  return static_cast<uint32_t>(GetCurrentProcessId());
#else
  return static_cast<uint32_t>(getpid());
#endif
}

// Nonblocking cross-process OS lock. Automatically released by the OS if a process dies.
class OsLock {
public:
#if defined(_WIN32)
  explicit OsLock(const std::filesystem::path& lock_file_path) {
    handle_ = CreateFileW(
        lock_file_path.c_str(),
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        nullptr,
        OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        nullptr);
    if (handle_ == INVALID_HANDLE_VALUE) {
      return;
    }
    OVERLAPPED ov{};
    if (LockFileEx(handle_, LOCKFILE_EXCLUSIVE_LOCK | LOCKFILE_FAIL_IMMEDIATELY, 0, 1, 0, &ov)) {
      locked_ = true;
    } else {
      CloseHandle(handle_);
      handle_ = INVALID_HANDLE_VALUE;
    }
  }

  ~OsLock() {
    if (locked_ && handle_ != INVALID_HANDLE_VALUE) {
      OVERLAPPED ov{};
      UnlockFileEx(handle_, 0, 1, 0, &ov);
    }
    if (handle_ != INVALID_HANDLE_VALUE) {
      CloseHandle(handle_);
    }
  }
#else
  explicit OsLock(const std::filesystem::path& lock_file_path) {
    fd_ = open(lock_file_path.c_str(), O_RDWR | O_CREAT, 0666);
    if (fd_ < 0) {
      return;
    }
    if (flock(fd_, LOCK_EX | LOCK_NB) == 0) {
      locked_ = true;
    } else {
      close(fd_);
      fd_ = -1;
    }
  }

  ~OsLock() {
    if (locked_ && fd_ >= 0) {
      flock(fd_, LOCK_UN);
    }
    if (fd_ >= 0) {
      close(fd_);
    }
  }
#endif

  bool is_locked() const noexcept {
    return locked_;
  }

  OsLock(const OsLock&) = delete;
  OsLock& operator=(const OsLock&) = delete;

private:
#if defined(_WIN32)
  HANDLE handle_ = INVALID_HANDLE_VALUE;
#else
  int fd_ = -1;
#endif
  bool locked_ = false;
};

// Cache file names are ASCII. path::string() can throw on Windows for a name outside the
// active code page, so names are read from the native form and anything else is skipped.
inline bool ascii_file_name(const std::filesystem::path& path, std::string& name) {
  const std::filesystem::path file_name = path.filename();  // owns the native string
  const auto& native = file_name.native();
  name.clear();
  name.reserve(native.size());
  for (const auto character : native) {
    using Unit = std::make_unsigned_t<std::filesystem::path::value_type>;
    const auto code = static_cast<Unit>(character);
    if (code == 0 || code > 0x7f) {
      return false;
    }
    name.push_back(static_cast<char>(code));
  }
  return true;
}

// Thread-safe stats counters for telemetry and testing.
struct Stats {
  uint64_t hits = 0;
  uint64_t misses = 0;
  uint64_t writes = 0;
};

// Reusable derived result cache implementation.
class Cache {
public:
  Cache(const std::filesystem::path& root, uint64_t cap = kDefaultCapacityBytes,
        bool enabled = true, std::size_t entry_limit = kMaximumCacheEntries)
      : root_(root), cap_(cap), enabled_(enabled && !root.empty()),
        entry_limit_(std::min(entry_limit, kMaximumCacheEntries)) {
    if (cap_ == 0 || root_.empty() || entry_limit_ == 0) {
      enabled_ = false;
    }
  }

  bool is_enabled() const noexcept {
    return enabled_;
  }

  const std::filesystem::path& root() const noexcept {
    return root_;
  }

  uint64_t cap() const noexcept {
    return cap_;
  }

  Stats stats() const noexcept {
    return Stats{hits_.load(std::memory_order_relaxed),
                 misses_.load(std::memory_order_relaxed),
                 writes_.load(std::memory_order_relaxed)};
  }

  void reset_stats() noexcept {
    hits_.store(0, std::memory_order_relaxed);
    misses_.store(0, std::memory_order_relaxed);
    writes_.store(0, std::memory_order_relaxed);
  }

  // Configure before starting concurrent decoding. Reads/writes may run in
  // parallel after setup; the frontend does not change a live cache's root.
  void reconfigure(const std::filesystem::path& root, uint64_t cap, bool enabled) {
    std::lock_guard<std::mutex> lock(config_mutex_);
    root_ = root;
    cap_ = cap;
    enabled_ = enabled && !root.empty() && (cap > 0) && entry_limit_ > 0;
  }

  // Reads payload from cache directly into caller-supplied buffer out.
  // Performs all header, file size, and SHA256 integrity checks.
  // Returns true on hit; any mismatch or error returns false (miss).
  bool read(const std::string& key, void* out, std::size_t expected_size) noexcept {
    platform::loading::Measure timing(platform::loading::Work::cache_read, expected_size);
    if (!enabled_ || !is_valid_key(key)) {
      misses_.fetch_add(1, std::memory_order_relaxed);
      return false;
    }
    if (out == nullptr && expected_size != 0) {
      misses_.fetch_add(1, std::memory_order_relaxed);
      return false;
    }
    if (expected_size > kMaxEntryPayloadBytes) {
      misses_.fetch_add(1, std::memory_order_relaxed);
      return false;
    }

    try {
      std::filesystem::path entry_path;
      {
        std::lock_guard<std::mutex> lock(config_mutex_);
        if (root_.empty()) {
          misses_.fetch_add(1, std::memory_order_relaxed);
          return false;
        }
        entry_path = root_ / (key + ".bin");
      }

      std::error_code ec;
      const auto status = std::filesystem::symlink_status(entry_path, ec);
      if (ec || !std::filesystem::is_regular_file(status) || std::filesystem::is_symlink(status)) {
        misses_.fetch_add(1, std::memory_order_relaxed);
        return false;
      }

      const auto file_size = std::filesystem::file_size(entry_path, ec);
      if (ec) {
        misses_.fetch_add(1, std::memory_order_relaxed);
        return false;
      }

      // Exact file size check before opening/reading: header plus expected payload.
      const uint64_t expected_file_size = sizeof(EntryHeader) + expected_size;
      if (file_size != expected_file_size) {
        misses_.fetch_add(1, std::memory_order_relaxed);
        return false;
      }

      std::ifstream file(entry_path, std::ios::binary);
      if (!file.is_open()) {
        misses_.fetch_add(1, std::memory_order_relaxed);
        return false;
      }

      EntryHeader header{};
      file.read(reinterpret_cast<char*>(&header), sizeof(header));
      if (!file || static_cast<std::size_t>(file.gcount()) != sizeof(header)) {
        misses_.fetch_add(1, std::memory_order_relaxed);
        return false;
      }

      if (std::memcmp(header.magic, kEntryMagic, sizeof(kEntryMagic)) != 0 ||
          header.version != kEntryVersion ||
          header.payload_size != expected_size ||
          std::memcmp(header.key, key.data(), 64) != 0 ||
          !is_valid_key(std::string_view(header.payload_sha256, 64))) {
        misses_.fetch_add(1, std::memory_order_relaxed);
        return false;
      }

      if (expected_size > 0) {
        file.read(reinterpret_cast<char*>(out), expected_size);
        if (!file || static_cast<std::size_t>(file.gcount()) != expected_size) {
          misses_.fetch_add(1, std::memory_order_relaxed);
          return false;
        }

      }
      platform::integrity::Sha256 sha;
      sha.update(out, expected_size);
      const std::string actual_sha = sha.hex();
      if (std::memcmp(actual_sha.data(), header.payload_sha256, 64) != 0) {
        misses_.fetch_add(1, std::memory_order_relaxed);
        return false;
      }

      file.close();

      // Touch hit time so LRU eviction retains active entries.
      std::filesystem::last_write_time(
          entry_path, std::filesystem::file_time_type::clock::now(), ec);

      timing.hit = true;
      hits_.fetch_add(1, std::memory_order_relaxed);
      return true;
    } catch (...) {
      misses_.fetch_add(1, std::memory_order_relaxed);
      return false;
    }
  }

  // Vector overload for reading payload.
  bool read(const std::string& key, std::vector<uint8_t>& out, std::size_t expected_size) noexcept {
    if (expected_size > kMaxEntryPayloadBytes || !is_valid_key(key) || !enabled_) {
      misses_.fetch_add(1, std::memory_order_relaxed);
      return false;
    }
    try {
      out.resize(expected_size);
    } catch (...) {
      misses_.fetch_add(1, std::memory_order_relaxed);
      return false;
    }
    return read(key, out.data(), expected_size);
  }

  // Writes payload to cache atomically using staging and cross-process OS locking.
  // Evicts oldest entries if needed to respect capacity limits.
  bool write(const std::string& key, const void* data, std::size_t size) noexcept {
    platform::loading::Measure timing(platform::loading::Work::cache_write, size);
    if (!enabled_ || !is_valid_key(key)) {
      return false;
    }
    if (data == nullptr && size != 0) {
      return false;
    }
    if (size > kMaxEntryPayloadBytes) {
      return false;
    }

    const uint64_t entry_total_size = sizeof(EntryHeader) + size;

    try {
      std::filesystem::path current_root;
      uint64_t current_cap = 0;
      {
        std::lock_guard<std::mutex> lock(config_mutex_);
        if (root_.empty()) {
          return false;
        }
        current_root = root_;
        current_cap = cap_;
      }

      if (entry_total_size > current_cap) {
        return false;
      }

      std::error_code ec;
      std::filesystem::create_directories(current_root, ec);
      if (ec) {
        return false;
      }

      // Own the entire staging lifetime. A busy writer must not allocate another
      // large temporary file, and the next lock owner can recover crashed writes.
      OsLock os_lock(current_root / ".cache.lock");
      if (!os_lock.is_locked()) {
        return false;
      }

      const auto staging_dir = current_root / "staging";
      std::filesystem::create_directories(staging_dir, ec);
      if (ec) {
        return false;
      }
      std::size_t staged_count = 0;
      // Explicit increment(ec): a range-for's ++ throws on an iteration error.
      std::filesystem::directory_iterator staged(staging_dir, ec);
      for (; !ec && staged != std::filesystem::directory_iterator(); staged.increment(ec)) {
        const auto& item = *staged;
        if (++staged_count > 10000) {
          return false;
        }
        const auto status = item.symlink_status(ec);
        if (ec) {
          return false;
        }
        std::string name;
        if (!ascii_file_name(item.path(), name)) {
          continue;  // Not one of ours.
        }
        const bool owned_temporary = name.size() >= 72 && name[64] == '.' &&
            name.compare(name.size() - 4, 4, ".tmp") == 0 &&
            is_valid_key(std::string_view(name.data(), 64));
        if (std::filesystem::is_regular_file(status) && owned_temporary) {
          std::filesystem::remove(item.path(), ec);
          if (ec) {
            return false;
          }
        }
      }
      if (ec) {
        return false;
      }

      // Compute payload SHA-256 digest.
      platform::integrity::Sha256 sha;
      if (data != nullptr && size > 0) {
        sha.update(data, size);
      }
      const std::string payload_sha = sha.hex();

      EntryHeader header{};
      std::memcpy(header.magic, kEntryMagic, sizeof(kEntryMagic));
      header.version = kEntryVersion;
      std::memcpy(header.key, key.data(), 64);
      header.payload_size = size;
      std::memcpy(header.payload_sha256, payload_sha.data(), 64);

      // Write staging file with unique process ID and sequence number.
      static std::atomic<uint64_t> s_staging_seq{0};
      const auto pid = current_process_id();
      const auto seq = s_staging_seq.fetch_add(1, std::memory_order_relaxed);
      const auto staging_name = key + "." + std::to_string(pid) + "." + std::to_string(seq) + ".tmp";
      const auto staging_path = staging_dir / staging_name;
      struct StagingCleanup {
        std::filesystem::path path;
        ~StagingCleanup() {
          try {
            std::error_code ignored;
            std::filesystem::remove(path, ignored);
          } catch (...) {
            // A later lock owner retries cleanup after an interrupted write.
          }
        }
      } cleanup{staging_path};

      {
        std::ofstream staging_file(staging_path, std::ios::binary | std::ios::trunc);
        if (!staging_file.is_open()) {
          return false;
        }
        staging_file.write(reinterpret_cast<const char*>(&header), sizeof(header));
        if (data != nullptr && size > 0) {
          staging_file.write(reinterpret_cast<const char*>(data), size);
        }
        staging_file.flush();
        if (!staging_file.good()) {
          staging_file.close();
          std::filesystem::remove(staging_path, ec);
          return false;
        }
      }

      // Perform LRU scan and eviction under lock.
      struct EntryRecord {
        std::filesystem::path path;
        uint64_t size = 0;
        std::filesystem::file_time_type mtime;
      };

      std::vector<EntryRecord> entries;
      uint64_t total_size = 0;
      std::size_t scan_count = 0;
      static constexpr std::size_t kMaxScanEntries = 10000;

      std::filesystem::directory_iterator scanned(current_root, ec);
      for (; !ec && scanned != std::filesystem::directory_iterator(); scanned.increment(ec)) {
        const auto& dir_entry = *scanned;
        if (++scan_count > kMaxScanEntries) {
          return false;
        }
        const auto status = dir_entry.symlink_status(ec);
        if (ec) {
          return false;
        }
        if (!std::filesystem::is_regular_file(status)) {
          continue;
        }
        std::string filename;
        if (!ascii_file_name(dir_entry.path(), filename)) {
          continue;  // Foreign file; never counted or evicted.
        }
        if (filename.size() != 68 || filename.rfind(".bin") != 64) {
          continue;
        }
        const std::string stem = filename.substr(0, 64);
        if (!is_valid_key(stem)) {
          continue;
        }
        const auto fsize = dir_entry.file_size(ec);
        if (ec) {
          return false;
        }
        const auto mtime = dir_entry.last_write_time(ec);
        if (ec) {
          return false;
        }
        if (stem == key) {
          // Destined to be overwritten by atomic rename; don't count twice in budget.
          continue;
        }
        entries.push_back({dir_entry.path(), fsize, mtime});
        if (fsize > std::numeric_limits<uint64_t>::max() - total_size) {
          return false;
        }
        total_size += fsize;
      }
      if (ec) {
        return false;
      }

      std::size_t remaining_entries = entries.size();
      if (total_size > current_cap - entry_total_size || remaining_entries >= entry_limit_) {
        std::sort(entries.begin(), entries.end(), [](const EntryRecord& a, const EntryRecord& b) {
          return a.mtime < b.mtime;
        });
        for (const auto& item : entries) {
          if (total_size <= current_cap - entry_total_size && remaining_entries < entry_limit_) {
            break;
          }
          std::filesystem::remove(item.path, ec);
          if (!ec) {
            --remaining_entries;
            if (total_size >= item.size) {
              total_size -= item.size;
            } else {
              total_size = 0;
            }
          }
        }
      }
      // Windows can refuse removal while a reader owns a file. Skipping this
      // write preserves the cap without disturbing either the reader or loading.
      if (total_size > current_cap - entry_total_size || remaining_entries >= entry_limit_) {
        return false;
      }

      // Atomic rename of staging file to target key.bin.
      const auto dest_path = current_root / (key + ".bin");
#if defined(_WIN32)
      if (!MoveFileExW(
              staging_path.c_str(),
              dest_path.c_str(),
              MOVEFILE_REPLACE_EXISTING)) {
        std::filesystem::remove(staging_path, ec);
        return false;
      }
#else
      std::filesystem::rename(staging_path, dest_path, ec);
      if (ec) {
        std::filesystem::remove(staging_path, ec);
        return false;
      }
#endif

      writes_.fetch_add(1, std::memory_order_relaxed);
      return true;
    } catch (...) {
      return false;
    }
  }

  bool write(const std::string& key, const std::vector<uint8_t>& data) noexcept {
    return write(key, data.data(), data.size());
  }

private:
  std::filesystem::path root_;
  uint64_t cap_ = kDefaultCapacityBytes;
  // Read by every decode thread while the frontend may reconfigure; atomic, not mutex-guarded.
  std::atomic<bool> enabled_{true};
  const std::size_t entry_limit_;
  std::mutex config_mutex_;
  std::atomic<uint64_t> hits_{0};
  std::atomic<uint64_t> misses_{0};
  std::atomic<uint64_t> writes_{0};
};

// Parses environment capacity limits between 16 and 8192 MB (default 2048 MB).
inline uint64_t parse_cache_cap_env() noexcept {
  const char* env = std::getenv("MW3_DISK_CACHE_MAX_MB");
  if (env == nullptr || env[0] == '\0') {
    env = std::getenv("MW3_DISK_CACHE_MB");
  }
  if (env == nullptr || env[0] == '\0') {
    env = std::getenv("MW3_CACHE_MAX_MB");
  }
  if (env != nullptr && env[0] != '\0') {
    char* end = nullptr;
    const unsigned long mb = std::strtoul(env, &end, 10);
    if (end != env && *end == '\0') {
      if (mb >= 16 && mb <= 8192) {
        return static_cast<uint64_t>(mb) * 1024ULL * 1024ULL;
      }
    }
  }
  return kDefaultCapacityBytes;
}

// Checks opt-out environment variable MW3_DISK_CACHE=0.
inline bool is_disk_cache_disabled_by_env() noexcept {
  const char* env = std::getenv("MW3_DISK_CACHE");
  if (env != nullptr) {
    if (std::strcmp(env, "0") == 0 ||
        std::strcmp(env, "false") == 0 ||
        std::strcmp(env, "FALSE") == 0 ||
        std::strcmp(env, "off") == 0 ||
        std::strcmp(env, "OFF") == 0 ||
        std::strcmp(env, "no") == 0 ||
        std::strcmp(env, "NO") == 0) {
      return true;
    }
  }
  return false;
}

// Internal holder for explicitly configured write directory.
inline std::filesystem::path& configured_write_directory_holder() {
  static std::filesystem::path s_dir;
  return s_dir;
}

inline std::mutex& configured_write_directory_mutex() {
  static std::mutex s_mtx;
  return s_mtx;
}

// Resolves the default cache root path according to platform specifications.
inline std::filesystem::path resolve_default_cache_root() {
  {
    std::lock_guard<std::mutex> lock(configured_write_directory_mutex());
    const auto& conf = configured_write_directory_holder();
    if (!conf.empty() && conf.is_absolute()) {
      if (conf.filename() == "derived-v1") {
        return conf;
      }
      if (conf.filename() == "cache") {
        return conf / "derived-v1";
      }
      return conf / "cache" / "derived-v1";
    }
  }

#if defined(_WIN32)
  const char* local_app = std::getenv("LOCALAPPDATA");
  if (local_app != nullptr && local_app[0] != '\0') {
    std::filesystem::path p(local_app);
    if (p.is_absolute()) {
      return p / "MW3Remaster" / "cache" / "derived-v1";
    }
  }
#else
  const char* xdg = std::getenv("XDG_CACHE_HOME");
  if (xdg != nullptr && xdg[0] != '\0') {
    std::filesystem::path p(xdg);
    if (p.is_absolute()) {
      return p / "mw3remaster" / "derived-v1";
    }
  }
  const char* home = std::getenv("HOME");
  if (home != nullptr && home[0] != '\0') {
    std::filesystem::path p(home);
    if (p.is_absolute()) {
      return p / ".cache" / "mw3remaster" / "derived-v1";
    }
  }
#endif

  // Never fall back to cwd or install folder; return empty path to disable.
  return {};
}

// Global default cache instance accessible across all components.
inline Cache& default_cache() {
  // The native frontend opts in after identifying its binary and user write
  // directory. Library users and asset-free tools must not read an old cached
  // answer instead of exercising their decoder, or write into a user's profile.
  static Cache s_default_cache({}, 0, false);
  return s_default_cache;
}

// Called by runtime main or initialization to explicitly configure the write directory.
inline void configure_write_directory(const std::filesystem::path& dir) {
  if (dir.empty() || !dir.is_absolute()) {
    return;
  }
  {
    std::lock_guard<std::mutex> lock(configured_write_directory_mutex());
    configured_write_directory_holder() = dir;
  }
  auto& c = default_cache();
  if (!is_disk_cache_disabled_by_env()) {
    std::filesystem::path target;
    if (dir.filename() == "derived-v1") {
      target = dir;
    } else if (dir.filename() == "cache") {
      target = dir / "derived-v1";
    } else {
      target = dir / "cache" / "derived-v1";
    }
    c.reconfigure(target, parse_cache_cap_env(), true);
  }
}

} // namespace platform::derived_cache

#endif // PLATFORM_DERIVED_CACHE_HPP
