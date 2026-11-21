// Regression and integration test suite for platform::derived_cache and verified_digest.
#include <chrono>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <thread>
#include <vector>

#include "platform/derived_cache.hpp"
#include "platform/verified_digest.hpp"

namespace {

static std::atomic<int> g_failures{0};

#define TEST_CHECK(cond)                                                                      \
  do {                                                                                        \
    if (!(cond)) {                                                                            \
      std::fprintf(stderr, "TEST FAILURE [%s:%d]: %s\n", __FILE__, __LINE__, #cond);         \
      g_failures.fetch_add(1);                                                                \
    }                                                                                         \
  } while (0)

std::filesystem::path create_clean_test_dir(const std::string& subname) {
  std::error_code ec;
  const auto temp_root = std::filesystem::temp_directory_path() /
                         ("mw3_test_derived_cache_" + std::to_string(platform::derived_cache::current_process_id()));
  const auto dir = temp_root / subname;
  std::filesystem::remove_all(dir, ec);
  std::filesystem::create_directories(dir, ec);
  return dir;
}

void test_hit_miss(const std::filesystem::path& root) {
  platform::derived_cache::Cache cache(root, 1024 * 1024);
  const std::vector<uint8_t> data = {0x10, 0x20, 0x30, 0x40, 0x50};
  const std::string k = platform::derived_cache::key(data.data(), data.size(), "test_hit_miss");

  std::vector<uint8_t> out;
  TEST_CHECK(!cache.read(k, out, data.size()));

  TEST_CHECK(cache.write(k, data.data(), data.size()));

  TEST_CHECK(cache.read(k, out, data.size()));
  TEST_CHECK(out == data);

  // Miss on nonexistent key
  const std::string missing_key(64, '0');
  TEST_CHECK(!cache.read(missing_key, out, data.size()));

  const auto empty_key = platform::derived_cache::key(nullptr, 0, "empty");
  TEST_CHECK(cache.write(empty_key, nullptr, 0));
  TEST_CHECK(cache.read(empty_key, out, 0));
  {
    std::fstream file(root / (empty_key + ".bin"),
        std::ios::in | std::ios::out | std::ios::binary);
    file.seekp(offsetof(platform::derived_cache::EntryHeader, payload_sha256));
    file.put('0'); // SHA256(empty) starts with 'e'; this remains valid hex.
    TEST_CHECK(file.good());
  }
  TEST_CHECK(!cache.read(empty_key, out, 0));
}

void test_input_domain_invalidation(const std::filesystem::path& root) {
  platform::derived_cache::Cache cache(root, 1024 * 1024);
  const std::vector<uint8_t> data1 = {1, 2, 3};
  const std::vector<uint8_t> data2 = {1, 2, 4};

  const std::string k_domain_a = platform::derived_cache::key(data1.data(), data1.size(), "domain_A");
  const std::string k_domain_b = platform::derived_cache::key(data1.data(), data1.size(), "domain_B");
  const std::string k_data2 = platform::derived_cache::key(data2.data(), data2.size(), "domain_A");

  TEST_CHECK(k_domain_a != k_domain_b);
  TEST_CHECK(k_domain_a != k_data2);

  TEST_CHECK(cache.write(k_domain_a, data1.data(), data1.size()));

  std::vector<uint8_t> out;
  TEST_CHECK(cache.read(k_domain_a, out, data1.size()));
  TEST_CHECK(!cache.read(k_domain_b, out, data1.size()));
  TEST_CHECK(!cache.read(k_data2, out, data2.size()));
}

void test_game_build_invalidation(const std::filesystem::path& root) {
  platform::derived_cache::Cache cache(root, 1024 * 1024);
  const std::vector<uint8_t> data{1, 2, 3};
  platform::derived_cache::configure_producer_identity("first-game-build");
  const auto first = platform::derived_cache::key(data.data(), data.size(), "build-test");
  TEST_CHECK(cache.write(first, data.data(), data.size()));
  platform::derived_cache::configure_producer_identity("other-game-build");
  const auto changed = platform::derived_cache::key(data.data(), data.size(), "build-test");
  TEST_CHECK(first != changed);
  std::vector<uint8_t> output;
  TEST_CHECK(!cache.read(changed, output, data.size()));
  platform::derived_cache::configure_producer_identity("");
}

void test_wrong_expected_size(const std::filesystem::path& root) {
  platform::derived_cache::Cache cache(root, 1024 * 1024);
  const std::vector<uint8_t> data(100, 0xAA);
  const std::string k = platform::derived_cache::key(data.data(), data.size(), "test_wrong_size");

  TEST_CHECK(cache.write(k, data.data(), data.size()));

  std::vector<uint8_t> out;
  TEST_CHECK(!cache.read(k, out, 99));
  TEST_CHECK(!cache.read(k, out, 101));
  TEST_CHECK(!cache.read(k, out, 0));
  TEST_CHECK(cache.read(k, out, 100));
  TEST_CHECK(out == data);
}

void test_corruption_truncation_rebuilt(const std::filesystem::path& root) {
  platform::derived_cache::Cache cache(root, 1024 * 1024);
  const std::vector<uint8_t> data = {1, 3, 5, 7, 9, 11, 13, 17};
  const std::string k = platform::derived_cache::key(data.data(), data.size(), "test_corruption");
  const auto entry_path = root / (k + ".bin");

  // 1. Header corruption
  TEST_CHECK(cache.write(k, data.data(), data.size()));
  {
    std::fstream f(entry_path, std::ios::in | std::ios::out | std::ios::binary);
    TEST_CHECK(f.is_open());
    f.seekp(0, std::ios::beg);
    f.put('X'); // Corrupt magic
    f.close();
  }
  std::vector<uint8_t> out;
  TEST_CHECK(!cache.read(k, out, data.size()));

  // Rebuilding over corrupted header must succeed
  TEST_CHECK(cache.write(k, data.data(), data.size()));
  TEST_CHECK(cache.read(k, out, data.size()));
  TEST_CHECK(out == data);

  // 2. Payload corruption (SHA mismatch)
  {
    std::fstream f(entry_path, std::ios::in | std::ios::out | std::ios::binary);
    TEST_CHECK(f.is_open());
    f.seekp(-1, std::ios::end);
    f.put(0xEE);
    f.close();
  }
  TEST_CHECK(!cache.read(k, out, data.size()));

  // Rebuild over corrupted payload must succeed
  TEST_CHECK(cache.write(k, data.data(), data.size()));
  TEST_CHECK(cache.read(k, out, data.size()));
  TEST_CHECK(out == data);

  // 3. Truncation
  std::error_code ec;
  const auto orig_size = std::filesystem::file_size(entry_path, ec);
  std::filesystem::resize_file(entry_path, orig_size - 2, ec);
  TEST_CHECK(!cache.read(k, out, data.size()));

  // Rebuild over truncated file must succeed
  TEST_CHECK(cache.write(k, data.data(), data.size()));
  TEST_CHECK(cache.read(k, out, data.size()));
  TEST_CHECK(out == data);
}

void test_oversize(const std::filesystem::path& root) {
  // Total capacity 500 bytes
  platform::derived_cache::Cache cache(root, 500);

  // Entry size exceeding capacity
  const std::vector<uint8_t> large_data(600, 0xFF);
  const std::string k = platform::derived_cache::key(large_data.data(), large_data.size(), "test_oversize");
  TEST_CHECK(!cache.write(k, large_data.data(), large_data.size()));

  std::vector<uint8_t> out;
  TEST_CHECK(!cache.read(k, out, large_data.size()));
  out.clear();
  TEST_CHECK(!cache.read(k, out, platform::derived_cache::kMaxEntryPayloadBytes + 1));
  TEST_CHECK(out.empty());
}

void test_unsafe_keys(const std::filesystem::path& root) {
  platform::derived_cache::Cache cache(root, 1024 * 1024);
  const std::vector<uint8_t> data = {1, 2, 3};

  const std::vector<std::string> invalid_keys = {
      "",
      "abc",
      std::string(63, 'a'),
      std::string(65, 'a'),
      "123456789012345678901234567890123456789012345678901234567890123Z",
      "../12345678901234567890123456789012345678901234567890123456789012",
      "123456789012345678901234567890123456789012345678901234567890123A",
  };

  std::vector<uint8_t> out;
  for (const auto& ik : invalid_keys) {
    TEST_CHECK(!platform::derived_cache::is_valid_key(ik));
    TEST_CHECK(!cache.write(ik, data.data(), data.size()));
    TEST_CHECK(!cache.read(ik, out, data.size()));
  }
}

void test_cap_and_lru_touch(const std::filesystem::path& root) {
  // Cap holds exactly 2 entries (each entry is EntryHeader + 16 bytes)
  const uint64_t entry_size = sizeof(platform::derived_cache::EntryHeader) + 16;
  const uint64_t cap = entry_size * 2;
  platform::derived_cache::Cache cache(root, cap);

  const std::vector<uint8_t> data1(16, 0x11);
  const std::vector<uint8_t> data2(16, 0x22);
  const std::vector<uint8_t> data3(16, 0x33);

  const std::string key1 = platform::derived_cache::key(data1.data(), data1.size(), "lru_domain1");
  const std::string key2 = platform::derived_cache::key(data2.data(), data2.size(), "lru_domain2");
  const std::string key3 = platform::derived_cache::key(data3.data(), data3.size(), "lru_domain3");

  TEST_CHECK(cache.write(key1, data1.data(), data1.size()));
  TEST_CHECK(cache.write(key2, data2.data(), data2.size()));

  // Assign controlled timestamps without sleeping
  const auto now = std::filesystem::file_time_type::clock::now();
  const auto t_old = now - std::chrono::hours(10);
  const auto t_mid = now - std::chrono::hours(5);

  const auto path1 = root / (key1 + ".bin");
  const auto path2 = root / (key2 + ".bin");

  std::error_code ec;
  std::filesystem::last_write_time(path1, t_old, ec);
  std::filesystem::last_write_time(path2, t_mid, ec);

  // Touch key1 via read: moves key1's last_write_time to ~now
  std::vector<uint8_t> out;
  TEST_CHECK(cache.read(key1, out, 16));
  TEST_CHECK(out == data1);

  // Write key3: triggers eviction. key2 has older last_write_time (t_mid) than key1 (~now),
  // so key2 must be evicted and key1 retained!
  TEST_CHECK(cache.write(key3, data3.data(), data3.size()));

  TEST_CHECK(!cache.read(key2, out, 16));
  TEST_CHECK(cache.read(key1, out, 16));
  TEST_CHECK(cache.read(key3, out, 16));

#if defined(_WIN32)
  // A live reader can prevent eviction on Windows; publishing must then stop.
  const auto locked_root = root / "locked-reader";
  platform::derived_cache::Cache locked_cache(locked_root, entry_size);
  TEST_CHECK(locked_cache.write(key1, data1.data(), data1.size()));
  const auto held_path = locked_root / (key1 + ".bin");
  const HANDLE reader = CreateFileW(held_path.c_str(), GENERIC_READ,
      FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
  TEST_CHECK(reader != INVALID_HANDLE_VALUE);
  TEST_CHECK(!locked_cache.write(key2, data2.data(), data2.size()));
  TEST_CHECK(!std::filesystem::exists(locked_root / (key2 + ".bin")));
  if (reader != INVALID_HANDLE_VALUE) CloseHandle(reader);
  TEST_CHECK(locked_cache.write(key2, data2.data(), data2.size()));
#endif

  // The previous process could have died with a complete or partial staging file.
  const auto orphan = root / "staging" / (key1 + ".12345.9.tmp");
  {
    std::ofstream file(orphan, std::ios::binary);
    file << "interrupted write";
    TEST_CHECK(file.good());
  }
  TEST_CHECK(cache.write(key1, data1.data(), data1.size()));
  TEST_CHECK(!std::filesystem::exists(orphan));

  // Tiny files can fill the metadata bound long before the byte budget.
  const auto count_root = root / "entry-count";
  platform::derived_cache::Cache count_cache(count_root, 1024 * 1024, true, 2);
  TEST_CHECK(count_cache.write(key1, data1.data(), data1.size()));
  TEST_CHECK(count_cache.write(key2, data2.data(), data2.size()));
  std::filesystem::last_write_time(count_root / (key1 + ".bin"), t_old, ec);
  std::filesystem::last_write_time(count_root / (key2 + ".bin"), t_mid, ec);
  TEST_CHECK(count_cache.read(key1, out, 16));
  TEST_CHECK(count_cache.write(key3, data3.data(), data3.size()));
  TEST_CHECK(!count_cache.read(key2, out, 16));
  TEST_CHECK(count_cache.read(key1, out, 16));
  TEST_CHECK(count_cache.read(key3, out, 16));
}

void test_lock_contention_and_recovery(const std::filesystem::path& root) {
  platform::derived_cache::Cache cache(root, 1024 * 1024);
  const std::vector<uint8_t> data = {1, 2, 3, 4};
  const std::string k = platform::derived_cache::key(data.data(), data.size(), "lock_test");

  std::error_code ec;
  std::filesystem::create_directories(root, ec);
  const auto lock_file = root / ".cache.lock";

  // Hold exclusive lock in this scope
  {
    platform::derived_cache::OsLock held_lock(lock_file);
    TEST_CHECK(held_lock.is_locked());

    // While locked, write attempt skips cleanly and returns false
    const bool write_result = cache.write(k, data.data(), data.size());
    TEST_CHECK(!write_result);
  }

  // Once released, write succeeds
  const bool write_success = cache.write(k, data.data(), data.size());
  TEST_CHECK(write_success);

  std::vector<uint8_t> out;
  TEST_CHECK(cache.read(k, out, data.size()));
  TEST_CHECK(out == data);
}

void test_opt_out_environment(const std::filesystem::path& root) {
  platform::derived_cache::Cache indep_cache(root, 1024 * 1024);
  const std::vector<uint8_t> data = {4, 5, 6};
  const std::string k = platform::derived_cache::key(data.data(), data.size(), "opt_out_test");

  TEST_CHECK(indep_cache.write(k, data.data(), data.size()));
  std::vector<uint8_t> out;
  TEST_CHECK(indep_cache.read(k, out, data.size()));

  // Test opt-out environment detection
#if defined(_WIN32)
  _putenv("MW3_DISK_CACHE=0");
#else
  setenv("MW3_DISK_CACHE", "0", 1);
#endif
  TEST_CHECK(platform::derived_cache::is_disk_cache_disabled_by_env());
  platform::derived_cache::configure_write_directory(root / "disabled");
  TEST_CHECK(!platform::derived_cache::default_cache().is_enabled());

  // Independent cache is NOT disabled by MW3_DISK_CACHE=0
  TEST_CHECK(indep_cache.read(k, out, data.size()));
  TEST_CHECK(indep_cache.write(k, data.data(), data.size()));

#if defined(_WIN32)
  _putenv("MW3_DISK_CACHE=");
#else
  unsetenv("MW3_DISK_CACHE");
#endif
}

void test_concurrent_reads_writes(const std::filesystem::path& root) {
  platform::derived_cache::Cache cache(root, 50 * 1024 * 1024);
  static constexpr int kNumThreads = 4;
  static constexpr int kIterations = 100;

  std::vector<std::thread> workers;
  workers.reserve(kNumThreads);

  for (int t = 0; t < kNumThreads; ++t) {
    workers.emplace_back([&cache, t]() {
      for (int i = 0; i < kIterations; ++i) {
        const std::vector<uint8_t> val = {
            static_cast<uint8_t>(t), static_cast<uint8_t>(i), 0xAA, 0xBB};
        const std::string k = platform::derived_cache::key(val.data(), val.size(), "concurrent_test");
        cache.write(k, val.data(), val.size());

        std::vector<uint8_t> readback;
        if (cache.read(k, readback, val.size())) {
          TEST_CHECK(readback == val);
        }
      }
    });
  }

  for (auto& w : workers) {
    if (w.joinable()) {
      w.join();
    }
  }
}

} // namespace

// Environment pack members: the full hash is reused only while the file is unchanged.
void test_verified_digest_reuse_and_invalidation(const std::filesystem::path& root) {
  std::filesystem::create_directories(root);
  const auto member = root / "member.bin";
  auto write_member = [&](char fill) {
    std::ofstream out(member, std::ios::binary | std::ios::trunc);
    const std::string bytes(4096, fill);
    out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
  };
  write_member('a');
  const auto first_truth = platform::integrity::sha256_file(member);

  // With the cache off every call hashes and nothing is stored.
  platform::derived_cache::default_cache().reconfigure({}, 0, false);
  TEST_CHECK(platform::verified_digest::sha256_file(member, 4096) == first_truth);

  platform::derived_cache::configure_write_directory(root / "cache");
  auto& cache = platform::derived_cache::default_cache();
  TEST_CHECK(cache.is_enabled());
  cache.reset_stats();
  TEST_CHECK(platform::verified_digest::sha256_file(member, 4096) == first_truth);
  TEST_CHECK(cache.stats().hits == 0 && cache.stats().writes == 1);
  TEST_CHECK(platform::verified_digest::sha256_file(member, 4096) == first_truth);
  TEST_CHECK(cache.stats().hits == 1);

  // Same size, new contents and a later write time: hashed again, never the old digest.
  write_member('b');
  std::filesystem::last_write_time(member, std::filesystem::last_write_time(member) +
                                               std::chrono::seconds(5));
  const auto second_truth = platform::integrity::sha256_file(member);
  TEST_CHECK(second_truth != first_truth);
  TEST_CHECK(platform::verified_digest::sha256_file(member, 4096) == second_truth);

  // A missing file is not remembered; the plain hash reports it as before.
  std::filesystem::remove(member);
  bool failed = false;
  try {
    (void)platform::verified_digest::sha256_file(member, 4096);
  } catch (const std::exception&) {
    failed = true;
  }
  TEST_CHECK(failed);
  cache.reconfigure({}, 0, false);
}

int main() {
  std::fprintf(stderr, "=== Starting mw3derived_cache_checks ===\n");
  TEST_CHECK(!platform::derived_cache::default_cache().is_enabled());

  const auto test_dir = create_clean_test_dir("main_tests");

  test_hit_miss(test_dir / "hit_miss");
  test_input_domain_invalidation(test_dir / "domain_inv");
  test_game_build_invalidation(test_dir / "build_inv");
  test_wrong_expected_size(test_dir / "wrong_size");
  test_corruption_truncation_rebuilt(test_dir / "corrupt_rebuilt");
  test_oversize(test_dir / "oversize");
  test_unsafe_keys(test_dir / "unsafe_keys");
  test_cap_and_lru_touch(test_dir / "lru_touch");
  test_lock_contention_and_recovery(test_dir / "lock_contention");
  test_opt_out_environment(test_dir / "opt_out");
  test_concurrent_reads_writes(test_dir / "concurrent");
  test_verified_digest_reuse_and_invalidation(test_dir / "verified_digest");

  std::error_code ec;
  std::filesystem::remove_all(test_dir, ec);

  if (g_failures == 0) {
    std::fprintf(stderr, "=== All mw3derived_cache_checks PASSED ===\n");
    return 0;
  }

  std::fprintf(stderr, "=== mw3derived_cache_checks FAILED (%d failures) ===\n", g_failures.load());
  return 1;
}
