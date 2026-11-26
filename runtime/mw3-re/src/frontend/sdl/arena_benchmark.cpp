#include "frontend/sdl/arena_benchmark.h"

#include <algorithm>
#include <cctype>
#include <charconv>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <limits>
#include <locale>
#include <numeric>
#include <set>
#include <stdexcept>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <wincodec.h>
#include <wrl/client.h>
#endif

#include "nlohmann-json/json.hpp"
#include "platform/sha256.hpp"

namespace sdlfe::benchmark {
namespace {

constexpr double kFullTurn = 6.28318530717958647692;
using Json = nlohmann::json;
using platform::integrity::sha256_file;

Json read_json(const std::filesystem::path &path) {
    std::ifstream input(path, std::ios::binary);
    if (!input)
        throw std::runtime_error("cannot open " + path.string());
    return Json::parse(input);
}

uint32_t integer(const Json &value, uint32_t maximum) {
    if (!value.is_number_integer() || value.get<uint64_t>() > maximum)
        throw std::runtime_error("integer out of range");
    return value.get<uint32_t>();
}

void check_version(const Json &document) {
    if (integer(document.at("version"), UINT32_MAX) != 1)
        throw std::runtime_error("unsupported benchmark format version");
}

double number(const Json &value) {
    const double result = value.get<double>();
    if (!std::isfinite(result))
        throw std::runtime_error("non-finite number");
    return result;
}

std::filesystem::path fixture(const std::filesystem::path &definition, const Json &value,
                              const std::string &hash) {
    const std::filesystem::path relative = value.get<std::string>();
    if (relative.empty() || relative.has_root_path())
        throw std::runtime_error("fixture path must be relative to the definition");
    const auto path = (definition.parent_path() / relative).lexically_normal();
    if (sha256_file(path) != hash)
        throw std::runtime_error("SHA-256 mismatch for " + path.string());
    return path;
}

std::string digest(const std::string &bytes) {
    platform::integrity::Sha256 sha;
    sha.update(bytes.data(), bytes.size());
    return sha.hex();
}

} // namespace

CameraTrack load_camera(const std::filesystem::path &path, double end) {
    const Json document = read_json(path);
    check_version(document);
    const auto &keys = document.at("keys");
    if (!keys.is_array() || keys.empty())
        throw std::runtime_error("camera needs keys");
    CameraTrack track;
    for (const auto &key : keys) {
        CameraKey point;
        point.time = number(key.at("t"));
        point.yaw = std::remainder(number(key.at("yaw")), kFullTurn);
        point.pitch = number(key.at("pitch"));
        const auto &position = key.at("pos");
        if (!position.is_array() || position.size() != 3)
            throw std::runtime_error("camera position must have three coordinates");
        for (size_t axis = 0; axis < 3; ++axis)
            point.position[axis] = number(position[axis]);
        const auto fits_float = [](double value) {
            return std::abs(value) <= std::numeric_limits<float>::max();
        };
        if (!fits_float(point.pitch) ||
            !std::all_of(point.position.begin(), point.position.end(), fits_float))
            throw std::runtime_error("camera coordinate out of range");
        if (track.empty() ? point.time != 0 : point.time <= track.back().time)
            throw std::runtime_error("camera must start at zero and key times must increase");
        track.push_back(point);
    }
    if (track.back().time < end)
        throw std::runtime_error("camera ends before measurement");
    return track;
}

CameraKey sample_camera(const CameraTrack &track, double time) {
    auto next = std::upper_bound(track.begin(), track.end(), time,
                                 [](double time, const CameraKey &key) { return time < key.time; });
    if (next == track.begin())
        return track.front();
    if (next == track.end())
        return track.back();
    const auto &previous = *(next - 1);
    const double amount = (time - previous.time) / (next->time - previous.time);
    CameraKey result;
    result.time = time;
    result.pitch = previous.pitch + (next->pitch - previous.pitch) * amount;
    const double turn = std::remainder(next->yaw - previous.yaw, kFullTurn);
    result.yaw = previous.yaw + turn * amount;
    for (size_t axis = 0; axis < 3; ++axis)
        result.position[axis] =
            previous.position[axis] + (next->position[axis] - previous.position[axis]) * amount;
    return result;
}

Resolution parse_resolution(std::string_view text) {
    Resolution size;
    const auto end = text.data() + text.size();
    auto width = std::from_chars(text.data(), end, size.width);
    if (width.ec != std::errc{} || width.ptr == end || *width.ptr != 'x')
        throw std::runtime_error("expected benchmark resolution WxH");
    const auto height = std::from_chars(width.ptr + 1, end, size.height);
    if (height.ec != std::errc{} || height.ptr != end || size.width < 640 || size.width > 7680 ||
        size.height < 480 || size.height > 4320)
        throw std::runtime_error("unsupported benchmark resolution");
    return size;
}

void require_window_mode(std::string_view mode, bool windowed, bool sized_window,
                         Resolution requested, Resolution window) {
    if (mode == "windowed") {
        if (!windowed || !sized_window || requested.width != window.width ||
            requested.height != window.height)
            throw std::runtime_error("windowed benchmark needs the requested --window size");
    } else if (mode == "fullscreen" || mode == "borderless") {
        if (windowed || sized_window)
            throw std::runtime_error("fullscreen benchmark uses the desktop window");
    } else {
        throw std::runtime_error("unknown benchmark window mode");
    }
}

void require_loaded_models(size_t expected_lods, size_t loaded_lods) {
    if (expected_lods != loaded_lods)
        throw std::runtime_error("benchmark prepared model bindings did not all load");
}

Pack read_pack(const std::filesystem::path &root) {
    const auto manifest = read_json(root / "pack.json");
    if (manifest.at("schema_version") != 2)
        throw std::runtime_error("benchmark pack needs a schema 2 manifest: " + root.string());
    return {manifest.at("id").get<std::string>(), manifest.at("name").get<std::string>(),
            manifest.at("native_payload").at("profile").get<std::string>(), content_sha256(root)};
}

namespace {
constexpr std::array<std::string_view, 6> shot_names{"chase", "orbit", "side",
                                                     "front", "high",  "low"};

std::vector<CameraShot> read_sequence(const Json &camera, double end) {
    const auto &records = camera.at("shots");
    if (!records.is_array() || records.empty())
        throw std::runtime_error("camera needs a shot sequence");
    std::vector<CameraShot> shots;
    double start = 0;
    bool has_orbit = false;
    std::set<ShotType> angles;
    for (const auto &record : records) {
        const auto type = record.at("type").get<std::string>();
        const auto found = std::find(shot_names.begin(), shot_names.end(), type);
        if (found == shot_names.end())
            throw std::runtime_error("unknown camera shot: " + type);
        const auto mode = static_cast<ShotType>(found - shot_names.begin());
        if (shots.empty() && mode != ShotType::chase)
            throw std::runtime_error("camera sequence must start with chase");
        if (has_orbit && mode != ShotType::chase && mode != ShotType::orbit)
            angles.insert(mode);
        has_orbit |= mode == ShotType::orbit;
        const auto &subject = record.contains("mech") ? record.at("mech") : camera.at("subject");
        const int mech = integer(subject, INT32_MAX);
        const double duration = number(record.at("duration_seconds"));
        const double default_height = mode == ShotType::high ? 45 : mode == ShotType::low ? 3 : 12;
        if (record.contains("radius") && (mode != ShotType::orbit || record.contains("distance")))
            throw std::runtime_error("camera radius is only an alternative to orbit distance");
        const double distance = record.contains("radius")
                                    ? number(record.at("radius"))
                                    : number(record.value("distance", Json(40)));
        const double height = number(record.value("height", Json(default_height)));
        const double speed = number(record.value("degrees_per_second", Json(18)));
        if (duration < 5 || duration > 20 || distance <= 0 || distance > 1000 || height < 0 ||
            height > 1000 || std::abs(speed) > 360 || (mode == ShotType::orbit && speed == 0))
            throw std::runtime_error("invalid camera shot duration or pose");
        shots.push_back({mode, mech, start, duration, distance, height, speed});
        start += duration;
    }
    if (!has_orbit || angles.size() < 2)
        throw std::runtime_error("camera sequence needs an orbit followed by different angles");
    if (std::abs(start - end) > 1e-8)
        throw std::runtime_error("camera sequence must cover warm-up and measurement");
    return shots;
}

Json camera_settings(const Scene &scene) {
    if (scene.shots.empty())
        return {{"mode", "track"}, {"sha256", scene.camera_sha256}};
    Json shots = Json::array();
    for (const auto &shot : scene.shots)
        shots.push_back({{"type", shot_names[static_cast<size_t>(shot.type)]},
                         {"mech", shot.mech},
                         {"start_seconds", shot.start},
                         {"duration_seconds", shot.duration},
                         {"distance", shot.distance},
                         {"height", shot.height},
                         {"degrees_per_second", shot.orbit_degrees_per_second}});
    return {{"mode", "sequence"}, {"shots", std::move(shots)}};
}
} // namespace

const CameraShot &shot_at(const std::vector<CameraShot> &shots, double elapsed) {
    const auto next =
        std::upper_bound(shots.begin(), shots.end(), elapsed,
                         [](double time, const CameraShot &shot) { return time < shot.start; });
    return next == shots.begin() ? shots.front() : *(next - 1);
}

CameraKey sample_shot(const CameraShot &shot, const std::array<double, 3> &position, double heading,
                      double elapsed) {
    constexpr double pi = kFullTurn / 2;
    double angle = heading;
    switch (shot.type) {
    case ShotType::orbit:
        angle += (elapsed - shot.start) * shot.orbit_degrees_per_second * pi / 180;
        break;
    case ShotType::side:
        angle += pi / 2;
        break;
    case ShotType::front:
        angle += pi;
        break;
    case ShotType::chase:
    case ShotType::high:
    case ShotType::low:
        break;
    }
    const double horizontal = shot.type == ShotType::high ? shot.distance / 2 : shot.distance;
    CameraKey pose;
    pose.time = elapsed;
    pose.position = {position[0] + std::sin(angle) * horizontal, position[1] + shot.height,
                     position[2] + std::cos(angle) * horizontal};
    pose.yaw = std::atan2(position[0] - pose.position[0], position[2] - pose.position[2]);
    pose.pitch = std::atan2(shot.height - 6, horizontal);
    return pose;
}

Definition load_definition(const std::filesystem::path &path) {
    const Json document = read_json(path);
    check_version(document);
    Definition definition;
    const auto &scenes = document.at("scenes");
    if (!scenes.is_array() || scenes.empty())
        throw std::runtime_error("benchmark needs scenes");
    std::set<std::string> ids;
    for (const auto &record : scenes) {
        Scene scene;
        scene.id = record.at("id").get<std::string>();
        scene.map = record.at("map").get<std::string>();
        if (scene.id.empty() || scene.id.find_first_of(",\"\r\n") != std::string::npos ||
            scene.map.empty() || !ids.insert(scene.id).second)
            throw std::runtime_error("empty map or invalid or duplicate scene ID");
        scene.seed = integer(record.at("seed"), UINT32_MAX);
        scene.warmup = number(record.at("warmup_seconds"));
        scene.measured = number(record.at("measured_seconds"));
        if (scene.warmup <= 0 || scene.measured <= 0 || !std::isfinite(scene.end()) ||
            scene.end() <= scene.warmup)
            throw std::runtime_error("invalid benchmark durations");
        scene.stress = record.at("stress").get<bool>();
        scene.log_sha256 = record.at("log_sha256").get<std::string>();
        if (record.contains("start_seconds")) {
            scene.start_seconds = number(record.at("start_seconds"));
            if (*scene.start_seconds < 0 || !std::isfinite(*scene.start_seconds + scene.end()) ||
                *scene.start_seconds + scene.end() <= *scene.start_seconds)
                throw std::runtime_error("invalid start_seconds");
        }
        scene.log = fixture(path, record.at("log"), scene.log_sha256);
        const auto &camera = record.at("camera");
        const auto mode = camera.value("mode", std::string("sequence"));
        if (mode == "sequence") {
            scene.shots = read_sequence(camera, scene.end());
        } else if (mode == "track") {
            scene.camera_sha256 = camera.at("sha256").get<std::string>();
            scene.camera = fixture(path, camera.at("file"), scene.camera_sha256);
            scene.track = load_camera(scene.camera, scene.end());
        } else {
            throw std::runtime_error("unknown benchmark camera mode");
        }
        definition.scenes.push_back(std::move(scene));
    }
    return definition;
}

std::string content_sha256(const std::filesystem::path &root) {
    const auto describe = [](const std::filesystem::path &path) {
        constexpr uintmax_t small_file_limit = 1024 * 1024;
        const auto bytes = std::filesystem::file_size(path);
        Json record = {{"bytes", bytes}};
        const auto stem = path.stem().string();
        const bool addressed =
            stem.size() == 64 && std::all_of(stem.begin(), stem.end(),
                                             [](unsigned char c) { return std::isxdigit(c) != 0; });
        if (!addressed && bytes < small_file_limit)
            record["sha256"] = sha256_file(path);
        return record;
    };
    if (std::filesystem::is_regular_file(root)) {
        auto file = describe(root);
        file["name"] = root.filename().u8string();
        return digest(file.dump());
    }

    const auto manifest = root / "pack.json";
    Json members = Json::object();
    for (const auto &entry : std::filesystem::recursive_directory_iterator(root)) {
        if (entry.is_symlink())
            throw std::runtime_error("cannot fingerprint a linked asset: " + entry.path().string());
        if (entry.is_regular_file() && entry.path() != manifest)
            members[entry.path().lexically_relative(root).generic_u8string()] =
                describe(entry.path());
    }
    platform::integrity::Sha256 sha;
    if (std::filesystem::is_regular_file(manifest)) {
        std::ifstream input(manifest, std::ios::binary);
        if (!input)
            throw std::runtime_error("cannot open " + manifest.string());
        const std::string bytes{std::istreambuf_iterator<char>(input), {}};
        if (input.bad())
            throw std::runtime_error("cannot read " + manifest.string());
        sha.update(bytes.data(), bytes.size());
    }
    const char separator = 0;
    sha.update(&separator, 1);
    const auto files = members.dump();
    sha.update(files.data(), files.size());
    return sha.hex();
}

void require_empty_output(const std::filesystem::path &path) {
    if (path.empty() || (std::filesystem::exists(path) && (!std::filesystem::is_directory(path) ||
                                                           !std::filesystem::is_empty(path))))
        throw std::runtime_error("benchmark output must be a new or empty directory");
}

double monotonic_seconds() {
    return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch())
        .count();
}

double EpochClock::elapsed() const { return now_() - epoch(); }

std::optional<double> process_creation_epoch() {
#ifdef _WIN32
    FILETIME creation{}, exit{}, kernel{}, user{}, wall{};
    if (!GetProcessTimes(GetCurrentProcess(), &creation, &exit, &kernel, &user))
        return {};
    GetSystemTimePreciseAsFileTime(&wall);
    const double now = monotonic_seconds();
    const auto ticks = [](FILETIME time) {
        return (uint64_t{time.dwHighDateTime} << 32) | time.dwLowDateTime;
    };
    if (ticks(wall) < ticks(creation))
        return {};
    return now - double(ticks(wall) - ticks(creation)) / 10000000.0;
#else
    return {};
#endif
}

void Measurements::invalidate(FrameTag frame, std::string reason) {
    if (!failure_)
        failure_ = InvalidFrame{frame, std::move(reason)};
}

void Measurements::complete(FrameTag frame, double elapsed) {
    if (frame.sequence != completed_ + 1 || !std::isfinite(elapsed) || elapsed < 0 ||
        elapsed < previous_completion_) {
        invalidate(frame, "invalid present sequence or completion time");
        return;
    }
    ++completed_;
    if (elapsed < warmup_) {
        ++warmup_count_;
    } else if (elapsed < warmup_ + measured_) {
        PresentSample sample{frame, elapsed, {}};
        if (previous_completion_ >= warmup_)
            sample.interval_ms = (elapsed - previous_completion_) * 1000;
        samples_.push_back(sample);
    }
    previous_completion_ = elapsed;
}

void Measurements::finish(uint64_t submitted) {
    if (submitted != completed_)
        invalidate({completed_ + 1, 0}, "missing present after final drain");
    if (!warmup_count_ || samples_.size() < 2)
        invalidate({}, "need at least one warm-up and two measured presents");
}

std::optional<Statistics> Measurements::statistics() const {
    if (failure_ || !warmup_count_ || samples_.size() < 2)
        return {};
    std::vector<double> intervals;
    for (const auto &sample : samples_)
        if (sample.interval_ms)
            intervals.push_back(*sample.interval_ms);
    std::sort(intervals.begin(), intervals.end());
    const auto rank = [&](size_t percent) {
        return intervals[(intervals.size() * percent + 99) / 100 - 1];
    };
    const size_t tail = (intervals.size() + 99) / 100;
    const double slowest = std::accumulate(intervals.end() - tail, intervals.end(), 0.0);
    return Statistics{std::accumulate(intervals.begin(), intervals.end(), 0.0) / intervals.size(),
                      rank(50),
                      rank(95),
                      rank(99),
                      samples_.size() / measured_,
                      slowest > 0 ? 1000 * tail / slowest : 0};
}

StrictPlayback::StrictPlayback(std::vector<float> times, double start, std::function<double()> now)
    : times_(std::move(times)), start_(start), now_(std::move(now)) {
    if (times_.empty())
        throw std::runtime_error("strict benchmark window has no recorded state ticks");
    frames_.reserve(times_.size());
}

void hash_strict_pixels(StrictPresent &present, const uint8_t *pixels, size_t pixel_bytes,
                        bool rgba, bool capture) {
    present.pixel_hash.clear();
    present.capture_bgra.clear();
    if (pixel_bytes == 0 || pixel_bytes % 4 != 0)
        return;

    constexpr uint64_t prime = 1099511628211ULL;
    uint64_t hash = 14695981039346656037ULL;
    const size_t blue = rgba ? 2 : 0;
    const size_t red = rgba ? 0 : 2;
    if (capture)
        present.capture_bgra.resize(pixel_bytes);
    for (size_t offset = 0; offset < pixel_bytes; offset += 4) {
        const std::array<uint8_t, 4> bgra{pixels[offset + blue], pixels[offset + 1],
                                         pixels[offset + red], pixels[offset + 3]};
        for (uint8_t channel : bgra)
            hash = (hash ^ channel) * prime;
        if (capture)
            std::copy(bgra.begin(), bgra.end(), present.capture_bgra.data() + offset);
    }
    constexpr char digits[] = "0123456789abcdef";
    present.pixel_hash.resize(16);
    for (auto digit = present.pixel_hash.rbegin(); digit != present.pixel_hash.rend(); ++digit) {
        *digit = digits[hash & 0xf];
        hash >>= 4;
    }
}

FrameTag StrictPlayback::pending_frame() const {
    return issued_ > frames_.size() ? FrameTag{issued_, times_[issued_ - 1], {}} : FrameTag{};
}

std::optional<StrictTick> StrictPlayback::next(const PresentSource &wait) {
    return advance(wait_for_pending(wait));
}

std::optional<StrictPresent> StrictPlayback::wait_for_pending(const PresentSource &wait) const {
    if (!pending_frame().sequence)
        return {};
    const double deadline = now_() + kStrictPresentTimeoutSeconds;
    auto present = wait(deadline);
    if (now_() > deadline)
        return {};
    return present;
}

std::optional<StrictTick> StrictPlayback::advance(std::optional<StrictPresent> present) {
    if (const auto pending = pending_frame(); pending.sequence) {
        if (!present)
            throw std::runtime_error("timed out waiting for strict worker present");
        if (present->sequence != pending.sequence)
            throw std::runtime_error("strict worker present sequence mismatch");
        const auto &receipt = present->receipt;
        if (receipt.acquire_result != 0 || receipt.present_result != 0)
            throw std::runtime_error(
                "strict Vulkan acquire/present failed: " + std::to_string(receipt.acquire_result) +
                "/" + std::to_string(receipt.present_result));
        if (!receipt.same_swapchain)
            throw std::runtime_error("strict Vulkan swapchain changed");
        if (!receipt.resident || receipt.present_count != 1)
            throw std::runtime_error("strict tick requires exactly one resident worker present");
        if (present->pixel_hash.empty())
            throw std::runtime_error("strict worker present has no pixel hash");
        frames_.push_back(std::move(*present));
    }
    if (finished())
        return {};
    const size_t index = issued_++;
    const double time = times_[index];
    const double previous = index == 0 ? start_ : times_[index - 1];
    return StrictTick{index, time, time - start_, time - previous};
}

Run::Run(Scene selected, double log_start, int window_width, int window_height,
         std::filesystem::path output, std::optional<double> process_epoch,
         std::function<double()> now)
    : scene(std::move(selected)), log_start_time(log_start), width(window_width),
      height(window_height), output_(std::move(output)), process_epoch_(process_epoch),
      clock_(std::move(now)), measurements_(scene.warmup, scene.measured) {
    require_empty_output(output_);
    settings = {{"scene", scene.id},
                {"map", scene.map},
                {"seed", std::to_string(scene.seed)},
                {"log_sha256", scene.log_sha256}};
}

void Run::record_present(FrameTag frame, const PresentReceipt &receipt) {
    std::lock_guard lock(mutex_);
    if (!receipt.resident || receipt.acquire_result != 0 || receipt.present_result != 0 ||
        receipt.present_count != 1) {
        measurements_.invalidate(
            frame, "resident acquire/present failed: " + std::to_string(receipt.acquire_result) +
                       "/" + std::to_string(receipt.present_result));
    } else if (!receipt.same_swapchain) {
        measurements_.invalidate(frame, "Vulkan swapchain changed");
    } else {
        measurements_.complete(frame, receipt.timestamp - clock_.epoch());
    }
}

void Run::enable_strict(std::vector<float> times, std::optional<size_t> capture) {
    strict_.emplace(std::move(times), log_start_time, [this] { return clock_.now(); });
    if (capture && *capture >= strict_->size())
        throw std::runtime_error("strict capture index is outside the recorded tick window");
    capture_tick_ = capture;
}

void Run::record_strict_present(StrictPresent present) {
    std::lock_guard lock(mutex_);
    strict_present_ = std::move(present);
}

std::optional<StrictPresent> Run::take_strict_present() {
    std::lock_guard lock(mutex_);
    return std::exchange(strict_present_, std::nullopt);
}

std::optional<StrictTick> Run::next_strict_tick(const StrictPlayback::PresentSource &wait) {
    try {
        if (failed())
            return {};
        auto present = strict_->wait_for_pending(wait);
        // The worker and window callbacks may invalidate the pending tick while
        // we wait. Accept its receipt under the same lock as invalidation.
        std::lock_guard lock(mutex_);
        if (strict_failure_)
            return {};
        return strict_->advance(std::move(present));
    } catch (const std::exception &error) {
        invalidate(strict_->pending_frame(), error.what());
        return {};
    }
}

void Run::invalidate(FrameTag frame, std::string reason) {
    std::lock_guard lock(mutex_);
    if (strict()) {
        if (!strict_failure_)
            strict_failure_ = InvalidFrame{frame, std::move(reason)};
    } else {
        measurements_.invalidate(frame, std::move(reason));
    }
}

bool Run::failed() const {
    std::lock_guard lock(mutex_);
    return strict() ? strict_failure_.has_value() : measurements_.failure().has_value();
}

#ifdef _WIN32
namespace {
void save_strict_png(const std::filesystem::path &path, unsigned width, unsigned height,
                     const std::vector<uint8_t> &bgra) {
    const auto check = [](HRESULT result, const char *operation) {
        if (FAILED(result))
            throw std::runtime_error(std::string("strict PNG: ") + operation + " failed (" +
                                     std::to_string(result) + ")");
    };
    const HRESULT apartment = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    if (apartment != RPC_E_CHANGED_MODE)
        check(apartment, "COM initialization");
    struct Apartment {
        bool owned;
        ~Apartment() {
            if (owned)
                CoUninitialize();
        }
    } guard{SUCCEEDED(apartment)};
    using Microsoft::WRL::ComPtr;
    ComPtr<IWICImagingFactory> factory;
    check(CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER,
                           IID_PPV_ARGS(factory.GetAddressOf())),
          "imaging factory");
    ComPtr<IWICStream> stream;
    check(factory->CreateStream(stream.GetAddressOf()), "create stream");
    check(stream->InitializeFromFilename(path.c_str(), GENERIC_WRITE), "open file");
    ComPtr<IWICBitmapEncoder> encoder;
    check(factory->CreateEncoder(GUID_ContainerFormatPng, nullptr, encoder.GetAddressOf()),
          "create encoder");
    check(encoder->Initialize(stream.Get(), WICBitmapEncoderNoCache), "initialize encoder");
    ComPtr<IWICBitmapFrameEncode> frame;
    check(encoder->CreateNewFrame(frame.GetAddressOf(), nullptr), "create image");
    check(frame->Initialize(nullptr), "initialize image");
    check(frame->SetSize(width, height), "set dimensions");
    WICPixelFormatGUID format = GUID_WICPixelFormat32bppBGRA;
    check(frame->SetPixelFormat(&format), "set pixel format");
    if (format != GUID_WICPixelFormat32bppBGRA)
        throw std::runtime_error("strict PNG: encoder does not accept BGRA8");
    check(frame->WritePixels(height, width * 4, static_cast<UINT>(bgra.size()),
                             const_cast<BYTE *>(bgra.data())),
          "write pixels");
    check(frame->Commit(), "commit image");
    check(encoder->Commit(), "commit file");
}
} // namespace
#endif

bool Run::write_strict_results() {
    if (!strict_->finished() && !strict_failure_)
        strict_failure_ =
            InvalidFrame{strict_->pending_frame(), "strict playback exited before final drain"};

    Json frames = Json::array();
    const auto &presents = strict_->frames();
    for (size_t index = 0; index < presents.size(); ++index)
        frames.push_back({{"tick", index},
                          {"time_seconds", strict_->time(index)},
                          {"pixel_hash", presents[index].pixel_hash}});

    if (capture_tick_ && *capture_tick_ < presents.size()) {
        const auto index = *capture_tick_;
        const std::string name = "tick-" + std::to_string(index) + ".png";
        const auto pending = output_ / (name + ".tmp");
        try {
#ifdef _WIN32
            const auto &pixels = presents[index].capture_bgra;
            if (pixels.size() != size_t(width) * height * 4)
                throw std::runtime_error("strict PNG: missing captured pixels");
            save_strict_png(pending, width, height, pixels);
            std::filesystem::rename(pending, output_ / name);
            frames[index]["capture"] = name;
#else
            throw std::runtime_error("strict PNG capture requires Windows");
#endif
        } catch (const std::exception &error) {
            std::error_code ignored;
            std::filesystem::remove(pending, ignored);
            if (!strict_failure_)
                strict_failure_ = InvalidFrame{{index + 1, strict_->time(index), {}}, error.what()};
        }
    }

    Json result = {{"version", 1},
                   {"mode", "strict"},
                   {"valid", !strict_failure_},
                   {"scene_id", scene.id},
                   {"log_sha256", scene.log_sha256},
                   {"width", width},
                   {"height", height},
                   {"pixel_hash_kind", "fnv1a64-swapchain-bgra8"},
                   {"expected_ticks", strict_->size()},
                   {"source_sha", source_sha},
                   {"executable_sha256", executable_sha256},
                   {"gpu", gpu},
                   {"vulkan_driver_version", driver},
                   {"settings", settings},
                   {"frames", std::move(frames)}};
    if (strict_failure_) {
        const auto &failure = *strict_failure_;
        result["failure"] = {{"reason", failure.reason}};
        if (failure.frame.sequence) {
            result["failure"]["tick"] = failure.frame.sequence - 1;
            result["failure"]["time_seconds"] = failure.frame.replay_time;
        }
        std::fprintf(stderr, "mw3: strict benchmark failed: %s\n", failure.reason.c_str());
    }

    const auto pending = output_ / "strict.json.tmp";
    std::ofstream output(pending, std::ios::binary);
    output.exceptions(std::ios::failbit | std::ios::badbit);
    output << result.dump(2) << '\n';
    output.close();
    std::filesystem::rename(pending, output_ / "strict.json");
    return !strict_failure_;
}

bool Run::write_results() {
    std::lock_guard lock(mutex_);
    if (!strict()) {
        if (!reached_end_)
            measurements_.invalidate({}, "playback exited before measurement ended");
        measurements_.finish(submitted_);
    }
    require_empty_output(output_);
    std::filesystem::create_directories(output_);
    const auto write_lock = output_ / ".writing";
    if (!std::filesystem::create_directory(write_lock))
        throw std::runtime_error("another writer owns the benchmark output");
    struct Unlock {
        const std::filesystem::path &path;
        ~Unlock() {
            std::error_code ignored;
            std::filesystem::remove(path, ignored);
        }
    } unlock{write_lock};
    for (const auto &entry : std::filesystem::directory_iterator(output_))
        if (entry.path() != write_lock)
            throw std::runtime_error("benchmark output changed after validation");

    if (strict())
        return write_strict_results();

    const auto csv_path = output_ / "frames.csv";
    std::ofstream csv(csv_path, std::ios::binary);
    csv.exceptions(std::ios::failbit | std::ios::badbit);
    csv.imbue(std::locale::classic());
    csv << "scene_id,frame_seq,replay_time_seconds,present_elapsed_seconds,interval_ms\n";
    csv << std::setprecision(std::numeric_limits<double>::max_digits10);
    for (const auto &sample : measurements_.samples()) {
        csv << scene.id << ',' << sample.frame.sequence << ',' << sample.frame.replay_time << ','
            << sample.completion << ',';
        if (sample.interval_ms)
            csv << *sample.interval_ms;
        csv << '\n';
    }
    csv.close();

    auto canonical = Json(settings);
    canonical["asset_fingerprint"] = "manifest-file-metadata-v1";
    canonical["packs"] = Json::array();
    for (const auto &pack : packs) {
        canonical["packs"].push_back({{"id", pack.id},
                                      {"name", pack.name},
                                      {"profile", pack.profile},
                                      {"sha256", pack.sha256},
                                      {"model_chassis", pack.model_chassis}});
    }
    canonical["prepared_chassis_count"] = prepared_chassis;
    canonical["log_start_seconds"] = log_start_time;
    canonical["camera"] = camera_settings(scene);
    canonical["warmup_seconds"] = scene.warmup;
    canonical["measured_seconds"] = scene.measured;
    canonical["stress"] = scene.stress;
    const auto &failure = measurements_.failure();
    const auto stats = measurements_.statistics();
    Json summary = {
        {"version", 1},
        {"scene_id", scene.id},
        {"valid", !failure},
        {"frames_sha256", sha256_file(csv_path)},
        {"settings", canonical},
        {"prepared_model_draws", prepared_model_draws},
        {"executable_sha256", executable_sha256},
        {"source_sha", source_sha},
        {"gpu", gpu},
        {"vulkan_driver_version", driver},
        {"video_memory_pressure", pressure},
        {"settings_sha256", digest(canonical.dump())},
        {"boundaries_seconds",
         {{"warmup_start", 0}, {"measured_start", scene.warmup}, {"measured_end", scene.end()}}},
        {"submitted_presents", submitted_},
        {"successful_presents", measurements_.completed_count()},
        {"warmup_presents", measurements_.warmup_count()},
        {"measured_presents", measurements_.samples().size()},
        {"intervals", measurements_.samples().empty() ? 0 : measurements_.samples().size() - 1},
        {"process_to_epoch_seconds", "unavailable"},
        {"scene_load_to_epoch_seconds", "unavailable"}};
    const auto summarize_effect = [&](unsigned EffectCounts::*field) {
        uint64_t total = 0;
        unsigned peak = 0;
        for (const auto &sample : measurements_.samples()) {
            const unsigned count = sample.frame.effects.*field;
            total += count;
            peak = std::max(peak, count);
        }
        const auto frames = measurements_.samples().size();
        return Json{{"max", peak}, {"mean", frames ? double(total) / frames : 0.0}};
    };
    summary["measured_effects"] = {
        {"active_effect_lights", summarize_effect(&EffectCounts::lights)},
        {"beams", summarize_effect(&EffectCounts::beams)},
        {"explosions", summarize_effect(&EffectCounts::explosions)}};
    if (armed())
        summary["monotonic_epoch_seconds"] = clock_.epoch();
    if (armed() && process_epoch_)
        summary["process_to_epoch_seconds"] = clock_.epoch() - *process_epoch_;
    if (armed() && scene_load_entry > 0)
        summary["scene_load_to_epoch_seconds"] = clock_.epoch() - scene_load_entry;
    if (stats)
        summary["statistics"] = {{"mean_ms", stats->mean},
                                 {"p50_ms", stats->p50},
                                 {"p95_ms", stats->p95},
                                 {"p99_ms", stats->p99},
                                 {"average_fps", stats->average_fps},
                                 {"low_1_percent_fps", stats->low_1_percent_fps}};
    if (failure) {
        summary["failure"] = {{"frame_seq", failure->frame.sequence},
                              {"replay_time_seconds", failure->frame.replay_time},
                              {"reason", failure->reason}};
        std::fprintf(stderr, "mw3: benchmark invalid at frame %llu (%.6f s): %s\n",
                     static_cast<unsigned long long>(failure->frame.sequence),
                     failure->frame.replay_time, failure->reason.c_str());
    }
    const auto pending = output_ / "summary.json.tmp";
    std::ofstream output(pending, std::ios::binary);
    output.exceptions(std::ios::failbit | std::ios::badbit);
    output << summary.dump(2) << '\n';
    output.close();
    std::filesystem::rename(pending, output_ / "summary.json");
    return !failure;
}

} // namespace sdlfe::benchmark
