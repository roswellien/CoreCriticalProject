#pragma once
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace mw34::capture_direct {
inline constexpr std::uint64_t max_files=200000, max_index=64ull*1024*1024;
inline constexpr std::uint64_t max_file=256ull*1024*1024, max_total=2ull*1024*1024*1024;
struct Options {
    // Empty resolves to current_path()/reports inside the preserved boundary.
    std::filesystem::path reports_root;
    std::uint64_t files_per_part=max_files;
    std::uint64_t bytes_per_part=max_total;
    std::uint64_t index_bytes_per_part=max_index;
    // Deterministic fixture fault only; defaults disabled. No game semantic credit.
    std::uint64_t fail_after_written_bytes=UINT64_MAX;
};
struct Part {
    std::filesystem::path bundle;
    std::string sha256,index_sha256;
    std::uint64_t logical_files=0,payload_bytes=0,bundle_bytes=0,index_bytes=0;
};
struct Receipt {
    std::filesystem::path directory,manifest;
    std::vector<Part> parts;
    std::uint64_t logical_files=0,payload_bytes=0;
    double emit_seconds=0,finalize_seconds=0;
};
// Useful to benchmark emitters using the same explicitly restricted path domain.
void validate_ascii_name(std::string_view logical_name);
// ASCII logical names are an explicit subset of the frozen reader's Unicode domain.
// The complete output directory is published once, after all parts finalize.
class Writer {
public:
    explicit Writer(const std::filesystem::path& output_directory,Options options={});
    ~Writer() noexcept;
    Writer(const Writer&)=delete;
    Writer& operator=(const Writer&)=delete;
    void append(std::string_view logical_name,const void* data,std::size_t size);
    void close_batch();
    const Receipt& finish();
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
