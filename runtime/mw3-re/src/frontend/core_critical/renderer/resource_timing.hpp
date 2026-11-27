#pragma once
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace mw34::timing {

// Opt-in CPU wall-clock timing for resource decoding, staging, and pipeline
// creation hitches. Enabled when MW3_CC_RESOURCE_TIMING=1 is set in the
// process environment. Disabled timers do not read a clock.
inline constexpr std::uint64_t hitch_threshold_nanoseconds = 8000000ULL;
inline constexpr std::uint64_t minimum_report_frame_interval = 60ULL;

inline bool resource_timing_requested() {
    static const bool enabled = [] {
        const char *value = std::getenv("MW3_CC_RESOURCE_TIMING");
        return value && std::strcmp(value, "1") == 0;
    }();
    return enabled;
}

inline double nanoseconds_to_milliseconds(std::uint64_t nanoseconds) {
    return static_cast<double>(nanoseconds) / 1000000.0;
}

class ScopedDuration {
  public:
    explicit ScopedDuration(std::uint64_t *target_nanoseconds) noexcept
        : target_nanoseconds_(target_nanoseconds),
          start_time_(target_nanoseconds
                          ? std::chrono::steady_clock::now()
                          : std::chrono::steady_clock::time_point{}) {}

    ScopedDuration(const ScopedDuration &) = delete;
    ScopedDuration &operator=(const ScopedDuration &) = delete;

    ~ScopedDuration() {
        if (!target_nanoseconds_)
            return;
        const auto elapsed = std::chrono::steady_clock::now() - start_time_;
        if (elapsed.count() > 0) {
            *target_nanoseconds_ += static_cast<std::uint64_t>(
                std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed)
                    .count());
        }
    }

  private:
    std::uint64_t *target_nanoseconds_{};
    std::chrono::steady_clock::time_point start_time_{};
};

// Rate-limited decision helper shared by producer and GPU presentation
// boundaries. Logs when enabled, any category in the presented frame exceeds
// 8 ms, and either no frame has logged yet or at least 60 presented frames
// have elapsed since the previous report.
struct HitchReportGate {
    bool has_reported{false};
    std::uint64_t last_reported_frame{0};

    bool should_report(bool enabled, std::uint64_t frame_sequence,
                       std::uint64_t primary_nanoseconds,
                       std::uint64_t secondary_nanoseconds) {
        if (!enabled)
            return false;
        const std::uint64_t maximum_nanoseconds =
            std::max(primary_nanoseconds, secondary_nanoseconds);
        if (maximum_nanoseconds <= hitch_threshold_nanoseconds)
            return false;
        if (has_reported &&
            frame_sequence - last_reported_frame < minimum_report_frame_interval)
            return false;
        has_reported = true;
        last_reported_frame = frame_sequence;
        return true;
    }
};

// Lets a periodic report through when resource timing is enabled and at least
// `interval` has passed on the steady clock since the last one (#518's texture
// memory line, every 3 seconds).
struct PeriodicReportGate {
    bool has_reported{false};
    std::chrono::steady_clock::time_point last_report{};

    bool should_report(bool enabled, std::chrono::steady_clock::time_point now,
                       std::chrono::steady_clock::duration interval) {
        if (!enabled)
            return false;
        if (has_reported && now - last_report < interval)
            return false;
        has_reported = true;
        last_report = now;
        return true;
    }
};

// Thread-owned producer counters for world normal page decode and first-use
// CPU texture copy/staging.
struct ProducerResourceTiming {
    bool enabled{resource_timing_requested()};
    std::uint64_t presented_frame_sequence{0};
    std::uint64_t page_decode_nanoseconds{0};
    std::uint64_t page_upload_nanoseconds{0};
    HitchReportGate report_gate{};

    explicit ProducerResourceTiming(bool enabled_override = resource_timing_requested())
        : enabled(enabled_override) {}

    std::uint64_t *page_decode_target() noexcept {
        return enabled ? &page_decode_nanoseconds : nullptr;
    }

    std::uint64_t *page_upload_target() noexcept {
        return enabled ? &page_upload_nanoseconds : nullptr;
    }

    bool finish_present(std::FILE *stream = stderr) noexcept {
        ++presented_frame_sequence;
        const std::uint64_t decode_ns = page_decode_nanoseconds;
        const std::uint64_t upload_ns = page_upload_nanoseconds;
        page_decode_nanoseconds = 0;
        page_upload_nanoseconds = 0;
        if (!report_gate.should_report(enabled, presented_frame_sequence,
                                       decode_ns, upload_ns))
            return false;
        if (stream) {
            // Integer formatting preserves guest FP flags and rounding modes.
            std::fprintf(
                stream,
                "[RESOURCE_TIMING] owner=producer frame=%llu "
                "page_decode_ms=%llu.%03llu page_upload_ms=%llu.%03llu\n",
                static_cast<unsigned long long>(presented_frame_sequence),
                static_cast<unsigned long long>(decode_ns / 1000000ULL),
                static_cast<unsigned long long>((decode_ns / 1000ULL) % 1000ULL),
                static_cast<unsigned long long>(upload_ns / 1000000ULL),
                static_cast<unsigned long long>((upload_ns / 1000ULL) % 1000ULL));
        }
        return true;
    }
};

// Thread-owned GPU renderer counters accumulated across all render packets in
// a logical presented frame. Measures CPU wall time (including driver waits)
// for graphics pipeline creation misses and changed texture allocation/staging/
// upload recording.
struct GpuResourceTiming {
    bool enabled{resource_timing_requested()};
    std::uint64_t presented_frame_sequence{0};
    std::uint64_t pipeline_nanoseconds{0};
    std::uint64_t texture_upload_nanoseconds{0};
    HitchReportGate report_gate{};

    explicit GpuResourceTiming(bool enabled_override = resource_timing_requested())
        : enabled(enabled_override) {}

    std::uint64_t *pipeline_target() noexcept {
        return enabled ? &pipeline_nanoseconds : nullptr;
    }

    std::uint64_t *texture_upload_target() noexcept {
        return enabled ? &texture_upload_nanoseconds : nullptr;
    }

    bool finish_present(std::FILE *stream = stderr) noexcept {
        ++presented_frame_sequence;
        const std::uint64_t pipe_ns = pipeline_nanoseconds;
        const std::uint64_t tex_ns = texture_upload_nanoseconds;
        pipeline_nanoseconds = 0;
        texture_upload_nanoseconds = 0;
        if (!report_gate.should_report(enabled, presented_frame_sequence,
                                       pipe_ns, tex_ns))
            return false;
        if (stream) {
            // Integer formatting preserves guest FP flags and rounding modes.
            std::fprintf(
                stream,
                "[RESOURCE_TIMING] owner=gpu frame=%llu "
                "pipeline_ms=%llu.%03llu texture_upload_ms=%llu.%03llu\n",
                static_cast<unsigned long long>(presented_frame_sequence),
                static_cast<unsigned long long>(pipe_ns / 1000000ULL),
                static_cast<unsigned long long>((pipe_ns / 1000ULL) % 1000ULL),
                static_cast<unsigned long long>(tex_ns / 1000000ULL),
                static_cast<unsigned long long>((tex_ns / 1000ULL) % 1000ULL));
        }
        return true;
    }
};

template <typename TimingOwner> class PresentBoundaryScope {
  public:
    explicit PresentBoundaryScope(TimingOwner &owner,
                                  std::FILE *stream = stderr) noexcept
        : owner_(owner), stream_(stream) {}

    PresentBoundaryScope(const PresentBoundaryScope &) = delete;
    PresentBoundaryScope &operator=(const PresentBoundaryScope &) = delete;

    ~PresentBoundaryScope() { owner_.finish_present(stream_); }

  private:
    TimingOwner &owner_;
    std::FILE *stream_;
};

} // namespace mw34::timing
