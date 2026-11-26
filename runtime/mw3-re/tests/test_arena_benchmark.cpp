#include "frontend/sdl/arena_benchmark.h"

#include <cmath>
#include <fstream>
#include <iterator>
#include <thread>
#include <tuple>

#include "check.h"
#include "nlohmann-json/json.hpp"
#include "platform/sha256.hpp"

namespace {

using namespace sdlfe::benchmark;
using Json = nlohmann::json;

struct Files {
    explicit Files(const char *name) : dir(std::filesystem::path(MW3_TEST_TMP) / name) {
        std::filesystem::remove_all(dir);
        std::filesystem::create_directories(dir);
    }

    void write(const char *name, const std::string &bytes) const {
        std::ofstream output(dir / name, std::ios::binary);
        output << bytes;
    }

    std::string read(const char *name) const {
        std::ifstream input(dir / name, std::ios::binary);
        return {std::istreambuf_iterator<char>(input), {}};
    }

    std::filesystem::path dir;
};

template <class Function> bool rejects(Function run) {
    try {
        run();
    } catch (const std::exception &) {
        return true;
    }
    return false;
}

const char *kCamera = R"({"version":1,"keys":[
  {"t":0,"pos":[0,10,20],"yaw":3,"pitch":0},
  {"t":3,"pos":[6,16,14],"yaw":-3,"pitch":1}
]})";

} // namespace

TEST(benchmark_epoch_uses_elapsed_time_at_any_cadence) {
    double now = 501;
    EpochClock clock([&] { return now; });
    EXPECT(!clock.armed());
    clock.arm();
    for (double time : {0.0, 0.012, 0.017, 0.6, 0.605, 2.0}) {
        now = 501 + time;
        EXPECT(std::abs(clock.elapsed() - time) < 1e-9);
    }
}

TEST(benchmark_camera_validation_and_shortest_arc) {
    Files files("benchmark-camera");
    files.write("camera.json", kCamera);
    auto track = load_camera(files.dir / "camera.json", 3);
    const auto mid = sample_camera(track, 1.5);
    EXPECT(mid.position[0] == 3 && mid.position[1] == 13 && mid.position[2] == 17);
    EXPECT(mid.pitch == 0.5);
    EXPECT(std::abs(mid.yaw - 3.141592653589793) < 1e-10);
    EXPECT(sample_camera(track, 0).yaw == 3 && sample_camera(track, 3).yaw == -3);
    EXPECT(rejects([&] { load_camera(files.dir / "camera.json", 3.01); }));

    for (
        const char *broken :
        {R"({"version":2,"keys":[]})",
         R"({"version":1,"keys":[{"t":1,"pos":[1,2,3],"yaw":0,"pitch":0}]})",
         R"({"version":1,"keys":[{"t":0,"pos":[1,2],"yaw":0,"pitch":0}]})",
         R"({"version":1,"keys":[{"t":0,"pos":[1,2,3],"yaw":0,"pitch":1e308}]})",
         R"({"version":1,"keys":[{"t":0,"pos":[0,0,0],"yaw":0,"pitch":0},{"t":0,"pos":[0,0,0],"yaw":0,"pitch":0}]})"}) {
        files.write("camera.json", broken);
        EXPECT(rejects([&] { load_camera(files.dir / "camera.json", 0); }));
    }
}

TEST(benchmark_definition_checks_order_sizes_seed_durations_and_hashes) {
    using platform::integrity::sha256_file;
    Files files("benchmark-definition");
    files.write("camera.json", kCamera);
    files.write("match.jsonl", "fixture bytes\n");
    const Json scene = {{"id", "first"},
                        {"map", "c1mp1"},
                        {"log", "match.jsonl"},
                        {"log_sha256", sha256_file(files.dir / "match.jsonl")},
                        {"camera",
                         {{"mode", "track"},
                          {"file", "camera.json"},
                          {"sha256", sha256_file(files.dir / "camera.json")}}},
                        {"seed", 7},
                        {"warmup_seconds", 1},
                        {"measured_seconds", 2},
                        {"stress", false}};
    Json second = scene;
    second["id"] = "second";
    const Json definition = {{"version", 1}, {"scenes", Json::array({scene, second})}};
    const auto read = [&](const Json &content) {
        files.write("benchmark.json", content.dump());
        return load_definition(files.dir / "benchmark.json");
    };
    const auto parsed = read(definition);
    EXPECT(parsed.scenes.size() == 2 && parsed.scenes[0].id == "first" &&
           parsed.scenes[1].id == "second");
    EXPECT(parsed.scenes[0].log == (files.dir / "match.jsonl").lexically_normal());

    for (const auto &entry : std::vector<std::pair<std::string, Json>>{
             {"seed", -1},
             {"seed", uint64_t{1} << 32},
             {"seed", 1.5},
             {"warmup_seconds", 0},
             {"measured_seconds", -1},
             {"measured_seconds", "NaN"},
             {"measured_seconds", 4},
             {"log_sha256", ""},
             {"camera", {{"mode", "track"}, {"file", "camera.json"}, {"sha256", "bad"}}},
             {"start_seconds", -1},
             {"start_seconds", "not a number"},
             {"log", std::filesystem::absolute(files.dir / "match.jsonl").string()}}) {
        Json unexpected = definition;
        unexpected["scenes"][0][entry.first] = entry.second;
        EXPECT(rejects([&] { read(unexpected); }));
    }
    Json unexpected = definition;
    unexpected["version"] = 2;
    EXPECT(rejects([&] { read(unexpected); }));
    unexpected = definition;
    unexpected["scenes"][1]["id"] = "first";
    EXPECT(rejects([&] { read(unexpected); }));
}

TEST(benchmark_measurement_uses_present_completion_boundaries) {
    Measurements score(1, 2);
    score.complete({1, 0}, 0);
    score.complete({2, 0.9}, 1);
    score.complete({3, 1.3}, 1.5);
    score.complete({4, 2.8}, 2.9);
    score.complete({5, 2.9}, 3);
    score.complete({6, 2.95}, 3.1);
    score.finish(6);
    EXPECT(!score.failure());
    EXPECT(score.warmup_count() == 1);
    const auto &frames = score.samples();
    EXPECT(frames.size() == 3);
    if (frames.size() != 3)
        return;
    EXPECT(frames[0].frame.sequence == 2 && !frames[0].interval_ms);
    EXPECT(frames[2].frame.sequence == 4);
    const auto stats = score.statistics();
    EXPECT(stats.has_value());
    if (!stats)
        return;
    EXPECT(stats->average_fps == 1.5);
    EXPECT(std::abs(stats->mean - 950) < 1e-8);
    EXPECT(stats->p50 == 500);
    EXPECT(std::abs(stats->p95 - 1400) < 1e-8 && stats->p95 == stats->p99);
    EXPECT(std::abs(stats->low_1_percent_fps - 1000.0 / 1400) < 1e-8);
}

TEST(benchmark_tail_size_rounds_up_and_missing_or_failed_presents_invalidate) {
    Measurements score(1, 1);
    score.complete({1, 0}, 0);
    for (uint64_t frame = 2; frame <= 101; ++frame)
        score.complete({frame, 1}, 1 + (frame - 2) * 0.001);
    score.complete({102, 1}, 1.102);
    score.complete({103, 1}, 1.111);
    score.finish(103);
    const auto stats = score.statistics();
    EXPECT(stats && std::abs(stats->low_1_percent_fps - 1000.0 / 6) < 1e-7);

    Measurements missing(1, 2);
    missing.complete({1, 0}, 0);
    missing.complete({2, 1}, 1);
    missing.complete({3, 2}, 2);
    missing.finish(4);
    EXPECT(missing.failure() && missing.failure()->frame.sequence == 4 && !missing.statistics());

    Measurements failed(1, 2);
    failed.invalidate({3, 1.25}, "suboptimal present");
    failed.finish(3);
    EXPECT(failed.failure() && failed.failure()->reason == "suboptimal present" &&
           failed.failure()->frame.replay_time == 1.25);

    Measurements duplicate(1, 2);
    duplicate.complete({1, 0}, 0);
    duplicate.complete({1, 0}, 0.5);
    EXPECT(duplicate.failure());
}

TEST(benchmark_output_drains_then_publishes_hash_bound_summary) {
    Files files("benchmark-results");
    Scene scene;
    scene.id = "authored";
    scene.warmup = 1;
    scene.measured = 2;
    double now = 100;
    const auto out = files.dir / "complete";
    Run run(scene, 0.03125, 640, 480, out, 97, [&] { return now; });
    run.scene_load_entry = 99;
    run.arm();
    EXPECT(run.replay_time(run.elapsed()) == 0.03125);
    run.record_present(run.submit(run.replay_time(0), {99, 99, 99}), {true, true, 0, 0, 1, 100.5});
    run.record_present(run.submit(run.replay_time(0.8125), {3, 0, 1}), {true, true, 0, 0, 1, 101});
    run.record_present(run.submit(run.replay_time(1.25), {5, 2, 3}), {true, true, 0, 0, 1, 101.5});
    const auto final = run.submit(run.replay_time(2.98), {99, 99, 99});
    std::thread in_flight([&] { run.record_present(final, {true, true, 0, 0, 1, 103}); });
    run.finish_window();
    in_flight.join();
    EXPECT(run.write_results());
    const auto csv = files.read("complete/frames.csv");
    EXPECT(csv.find("authored,2,0.84375") != std::string::npos);
    EXPECT(csv.find(",1,\nauthored,3,1.28125,1.5,500\n") != std::string::npos);
    EXPECT(csv.find("authored,4,") == std::string::npos);
    const Json summary = Json::parse(files.read("complete/summary.json"));
    EXPECT(summary["valid"] == true && summary["version"] == 1);
    EXPECT(summary["measured_effects"]["active_effect_lights"]["max"] == 5);
    EXPECT(summary["measured_effects"]["active_effect_lights"]["mean"] == 4);
    EXPECT(summary["measured_effects"]["beams"]["mean"] == 1);
    EXPECT(summary["measured_effects"]["explosions"]["mean"] == 2);
    EXPECT(summary["settings"]["log_start_seconds"] == 0.03125);
    EXPECT(summary["boundaries_seconds"]["measured_start"] == 1 &&
           summary["boundaries_seconds"]["measured_end"] == 3);
    EXPECT(summary["process_to_epoch_seconds"] == 3 && summary["scene_load_to_epoch_seconds"] == 1);
    EXPECT(summary["frames_sha256"] == platform::integrity::sha256_file(out / "frames.csv"));
    EXPECT(summary["settings_sha256"].get<std::string>().size() == 64);
    EXPECT(rejects([&] { Run again(scene, 0, 640, 480, out, {}); }));

    Run interrupted(scene, 0, 640, 480, files.dir / "interrupted", {});
    EXPECT(!interrupted.write_results());
    const Json invalid = Json::parse(files.read("interrupted/summary.json"));
    EXPECT(invalid["valid"] == false && !invalid.contains("statistics"));
    EXPECT(invalid["process_to_epoch_seconds"] == "unavailable");

    const auto partial = files.dir / "partial";
    std::filesystem::create_directory(partial);
    files.write("partial/frames.csv", "incomplete");
    EXPECT(rejects([&] { Run again(scene, 0, 640, 480, partial, {}); }));
    EXPECT(!std::filesystem::exists(partial / "summary.json"));
}

TEST(benchmark_invalid_resident_receipts_publish_failure) {
    Files files("benchmark-receipts");
    Scene scene;
    scene.id = "authored";
    scene.warmup = 1;
    scene.measured = 2;
    const std::vector<PresentReceipt> invalid = {
        {true, true, 0, 1000001003, 1, 101}, // VK_SUBOPTIMAL_KHR
        {true, true, -1000001004, 0, 0, 0},  // VK_ERROR_OUT_OF_DATE_KHR
        {false, true, 0, 0, 0, 0},           {true, false, 0, 0, 1, 101},
        {true, true, 0, 0, 2, 101},
    };
    for (size_t index = 0; index < invalid.size(); ++index) {
        const auto directory = "case-" + std::to_string(index);
        Run run(scene, 0, 640, 480, files.dir / directory, {}, [] { return 100.0; });
        run.arm();
        run.record_present(run.submit(0.5), invalid[index]);
        EXPECT(run.failed());
        run.finish_window();
        EXPECT(!run.write_results());
        const auto path = directory + "/summary.json";
        const Json summary = Json::parse(files.read(path.c_str()));
        EXPECT(summary["valid"] == false && summary["failure"]["frame_seq"] == 1 &&
               summary["failure"]["replay_time_seconds"] == 0.5);
    }
}

TEST(benchmark_window_modes_and_loaded_models) {
    const auto size = parse_resolution("3440x1440");
    EXPECT(size.width == 3440 && size.height == 1440);
    EXPECT(!rejects([&] { require_window_mode("fullscreen", false, false, size, {}); }));
    EXPECT(!rejects([&] { require_window_mode("borderless", false, false, size, {}); }));
    EXPECT(!rejects([&] { require_window_mode("windowed", true, true, size, size); }));
    EXPECT(rejects([&] { require_window_mode("fullscreen", true, true, size, size); }));
    EXPECT(rejects([&] { require_window_mode("windowed", true, true, size, {1280, 720}); }));
    EXPECT(rejects([&] { parse_resolution("3440x1440extra"); }));
    EXPECT(!rejects([&] { require_loaded_models(36, 36); }));
    EXPECT(!rejects([&] { require_loaded_models(0, 0); }));
    EXPECT(rejects([&] { require_loaded_models(36, 35); }));
}

TEST(benchmark_sequence_validates_shots_and_samples_each_camera_type) {
    const auto shot = [](ShotType type) {
        return CameraShot{type, 3, 10, 5, 40, type == ShotType::low ? 3.0 : 18.0, 90};
    };
    const std::array<double, 3> subject{100, 5, 200};
    const auto close = [](double actual, double expected) {
        return std::abs(actual - expected) < 1e-9;
    };
    for (const auto &entry :
         std::vector<std::pair<ShotType, std::array<double, 3>>>{{ShotType::chase, {100, 23, 240}},
                                                                 {ShotType::orbit, {140, 23, 200}},
                                                                 {ShotType::side, {140, 23, 200}},
                                                                 {ShotType::front, {100, 23, 160}},
                                                                 {ShotType::high, {100, 23, 220}},
                                                                 {ShotType::low, {100, 8, 240}}}) {
        const auto pose = sample_shot(shot(entry.first), subject, 0, 11);
        for (size_t axis = 0; axis < 3; ++axis)
            EXPECT(close(pose.position[axis], entry.second[axis]));
        EXPECT(entry.first == ShotType::low ? pose.pitch < 0 : pose.pitch > 0);
    }

    Files files("benchmark-sequence");
    files.write("match.jsonl", "fixture bytes");
    const Json shots = Json::array({
        {{"type", "chase"}, {"duration_seconds", 5}},
        {{"type", "orbit"}, {"duration_seconds", 7}, {"mech", 2}, {"degrees_per_second", -28}},
        {{"type", "front"}, {"duration_seconds", 8}},
        {{"type", "high"}, {"duration_seconds", 5}},
    });
    const Json scene = {{"id", "sequence"},
                        {"map", "c1mp1"},
                        {"log", "match.jsonl"},
                        {"log_sha256", platform::integrity::sha256_file(files.dir / "match.jsonl")},
                        {"camera", {{"subject", 3}, {"shots", shots}}},
                        {"seed", 7},
                        {"warmup_seconds", 5},
                        {"measured_seconds", 20},
                        {"start_seconds", 30},
                        {"stress", false}};
    const auto read = [&](const Json &camera_shots) {
        Json input = scene;
        input["camera"]["shots"] = camera_shots;
        files.write("def.json", Json{{"version", 1}, {"scenes", Json::array({input})}}.dump());
        return load_definition(files.dir / "def.json");
    };
    const auto parsed = read(shots);
    const auto &loaded = parsed.scenes.front();
    EXPECT(loaded.start_seconds == 30);
    EXPECT(shot_at(loaded.shots, 4.99).mech == 3 && shot_at(loaded.shots, 5).mech == 2);
    EXPECT(shot_at(loaded.shots, 12).type == ShotType::front);
    for (const auto &[index, key, value] :
         std::vector<std::tuple<size_t, std::string, Json>>{{0, "type", "side"},
                                                            {1, "type", "side"},
                                                            {2, "type", "unknown"},
                                                            {0, "duration_seconds", 4},
                                                            {1, "duration_seconds", 21},
                                                            {2, "duration_seconds", 7},
                                                            {1, "degrees_per_second", 0},
                                                            {1, "height", "inf"},
                                                            {1, "distance", 0},
                                                            {1, "mech", -1}}) {
        Json broken = shots;
        broken[index][key] = value;
        EXPECT(rejects([&] { read(broken); }));
    }
}

TEST(benchmark_pack_fingerprint_reads_metadata_and_small_non_payload_files) {
    Files files("benchmark-pack-fingerprint");
    files.write("pack.json", "{}");
    files.write("large.bin", std::string(1024 * 1024, 'x'));
    const auto addressed = std::string(64, 'a') + ".bin";
    files.write(addressed.c_str(), "first");
    files.write("settings.txt", "first");
    const auto original = content_sha256(files.dir);
    files.write("large.bin", std::string(1024 * 1024, 'y'));
    files.write(addressed.c_str(), "other");
    EXPECT(content_sha256(files.dir) == original);
    files.write("settings.txt", "other");
    const auto changed_settings = content_sha256(files.dir);
    EXPECT(changed_settings != original);
    files.write("pack.json", "{ }");
    const auto changed_manifest = content_sha256(files.dir);
    EXPECT(changed_manifest != changed_settings);
    files.write(addressed.c_str(), "longer");
    EXPECT(content_sha256(files.dir) != changed_manifest);
}
