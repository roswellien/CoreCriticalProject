#pragma once

#include <array>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace sdlfe::benchmark {

struct CameraKey {
    double time{}, yaw{}, pitch{};
    std::array<double, 3> position{};
};

using CameraTrack = std::vector<CameraKey>;
CameraTrack load_camera(const std::filesystem::path &path, double end);
CameraKey sample_camera(const CameraTrack &track, double time);

enum class ShotType { chase, orbit, side, front, high, low };
struct CameraShot {
    ShotType type{};
    int mech{};
    double start{}, duration{}, distance{}, height{}, orbit_degrees_per_second{};
};
const CameraShot &shot_at(const std::vector<CameraShot> &shots, double elapsed);
CameraKey sample_shot(const CameraShot &shot, const std::array<double, 3> &position, double heading,
                      double elapsed);

struct EffectCounts {
    unsigned lights{}, beams{}, explosions{};
};

struct Scene {
    std::string id, map, log_sha256, camera_sha256;
    std::filesystem::path log, camera;
    uint32_t seed{};
    double warmup{}, measured{};
    bool stress{};
    CameraTrack track;
    std::vector<CameraShot> shots;
    std::optional<double> start_seconds;

    double end() const { return warmup + measured; }
};

struct Definition {
    std::vector<Scene> scenes;
};

struct Resolution {
    int width{}, height{};
};
Resolution parse_resolution(std::string_view text);
void require_window_mode(std::string_view mode, bool windowed, bool sized_window,
                         Resolution requested, Resolution window);
void require_loaded_models(size_t expected_lods, size_t loaded_lods);

struct Pack {
    std::string id, name, profile, sha256;
    size_t model_chassis{};
};

Pack read_pack(const std::filesystem::path &root);

Definition load_definition(const std::filesystem::path &path);
std::string content_sha256(const std::filesystem::path &root);
void require_empty_output(const std::filesystem::path &path);

double monotonic_seconds();
std::optional<double> process_creation_epoch();
inline constexpr double kStrictPresentTimeoutSeconds = 20;

class EpochClock {
  public:
    explicit EpochClock(std::function<double()> now = monotonic_seconds) : now_(std::move(now)) {}
    void arm() { epoch_ = now_(); }
    bool armed() const { return epoch_.has_value(); }
    double epoch() const { return epoch_.value(); }
    double elapsed() const;
    double now() const { return now_(); }

  private:
    std::function<double()> now_;
    std::optional<double> epoch_;
};

struct FrameTag {
    uint64_t sequence{};
    double replay_time{};
    EffectCounts effects;
};

// Native WSI reports zero for VK_SUCCESS. Keep the raw results so a failed
// acquire or a suboptimal present remains distinguishable in the output.
struct PresentReceipt {
    bool resident{}, same_swapchain{};
    int acquire_result{}, present_result{};
    uint64_t present_count{};
    double timestamp{};
};

struct PresentSample {
    FrameTag frame;
    double completion{};
    std::optional<double> interval_ms;
};

struct InvalidFrame {
    FrameTag frame;
    std::string reason;
};

struct StrictTick {
    size_t index;
    double time, elapsed, delta;
};

struct StrictPresent {
    uint64_t sequence;
    PresentReceipt receipt;
    std::string pixel_hash;
    std::vector<uint8_t> capture_bgra;
};

void hash_strict_pixels(StrictPresent &present, const uint8_t *pixels, size_t pixel_bytes,
                        bool rgba, bool capture);

// The source waits for the pending worker job until the supplied monotonic
// deadline. Calling next() at the end still consumes the final receipt.
class StrictPlayback {
  public:
    using PresentSource = std::function<std::optional<StrictPresent>(double deadline)>;
    StrictPlayback(std::vector<float> times, double start,
                   std::function<double()> now = monotonic_seconds);
    std::optional<StrictTick> next(const PresentSource &wait);
    FrameTag pending_frame() const;
    bool finished() const { return frames_.size() == times_.size(); }
    size_t size() const { return times_.size(); }
    const auto &frames() const { return frames_; }
    double time(size_t index) const { return times_.at(index); }

  private:
    friend class Run;
    std::optional<StrictPresent> wait_for_pending(const PresentSource &wait) const;
    std::optional<StrictTick> advance(std::optional<StrictPresent> present);

    std::vector<float> times_;
    double start_;
    std::function<double()> now_;
    size_t issued_{};
    std::vector<StrictPresent> frames_;
};

struct Statistics {
    double mean{}, p50{}, p95{}, p99{}, average_fps{}, low_1_percent_fps{};
};

// The accumulator sees completions in worker order. The caller drains the last
// submitted job before checking that every submission completed.
class Measurements {
  public:
    Measurements(double warmup, double measured) : warmup_(warmup), measured_(measured) {}
    void complete(FrameTag frame, double elapsed);
    void invalidate(FrameTag frame, std::string reason);
    void finish(uint64_t submitted);
    std::optional<Statistics> statistics() const;
    const auto &samples() const { return samples_; }
    const auto &failure() const { return failure_; }
    uint64_t warmup_count() const { return warmup_count_; }
    uint64_t completed_count() const { return completed_; }

  private:
    double warmup_, measured_;
    uint64_t completed_{}, warmup_count_{};
    double previous_completion_ = -1;
    std::vector<PresentSample> samples_;
    std::optional<InvalidFrame> failure_;
};

using Settings = std::map<std::string, std::string>;

// The producer owns the epoch and tags. The worker reports completions and
// failures. A mutex protects the accumulator and preserves the first failure.
class Run {
  public:
    Run(Scene selected, double log_start_time, int width, int height, std::filesystem::path output,
        std::optional<double> process_epoch, std::function<double()> now = monotonic_seconds);

    const Scene scene;
    const double log_start_time;
    double replay_time(double elapsed) const { return log_start_time + elapsed; }
    const int width, height;
    Settings settings;
    std::vector<Pack> packs;
    size_t prepared_chassis{}, expected_model_lods{};
    uint64_t prepared_model_draws{};
    std::map<std::string, uint64_t> pressure;
    std::string executable_sha256, source_sha, gpu;
    uint32_t driver{};
    double scene_load_entry{};
    void arm() { clock_.arm(); }
    bool armed() const { return clock_.armed(); }
    double elapsed() const { return clock_.elapsed(); }
    FrameTag next_frame(double replay_time) const {
        if (strict_)
            return strict_->pending_frame();
        return {submitted_ + 1, replay_time, {}};
    }
    FrameTag submit(double replay_time, EffectCounts effects = {}) {
        return {++submitted_, replay_time, effects};
    }
    void record_present(FrameTag frame, const PresentReceipt &receipt);
    void enable_strict(std::vector<float> times, std::optional<size_t> capture);
    bool strict() const { return strict_.has_value(); }
    bool captures(uint64_t sequence) const {
        return capture_tick_ && *capture_tick_ == sequence - 1;
    }
    void record_strict_present(StrictPresent present);
    std::optional<StrictPresent> take_strict_present();
    std::optional<StrictTick> next_strict_tick(const StrictPlayback::PresentSource &wait);
    void invalidate(FrameTag frame, std::string reason);
    bool failed() const;
    void finish_window() { reached_end_ = true; }
    bool write_results();

  private:
    bool write_strict_results();
    std::filesystem::path output_;
    std::optional<double> process_epoch_;
    EpochClock clock_;
    uint64_t submitted_{};
    bool reached_end_{};
    mutable std::mutex mutex_;
    Measurements measurements_;
    std::optional<StrictPlayback> strict_;
    std::optional<size_t> capture_tick_;
    std::optional<StrictPresent> strict_present_;
    std::optional<InvalidFrame> strict_failure_;
};

} // namespace sdlfe::benchmark
