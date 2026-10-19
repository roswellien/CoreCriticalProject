#include "native-overrides/photo_replay_math.hpp"
#include <cassert>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <vector>

using namespace mw34::photo_replay;

static bool near_eq(float a, float b, float eps = 1e-4f) {
    return std::fabs(a - b) <= eps;
}

static void test_euler_mat3x4_roundtrip() {
    const float pitches[] = {-1.1f, -0.45f, 0.0f, 0.35f, 1.2f};
    const float yaws[]    = {-2.8f, -1.2f, 0.0f, 0.9f, 2.5f};
    const float rolls[]   = {-0.8f, -0.2f, 0.0f, 0.4f, 0.9f};
    const Vec3 pos{125.5f, 18.25f, -340.75f};

    for (float p : pitches) {
        for (float y : yaws) {
            for (float r : rolls) {
                const Mat3x4 m = euler_to_mat3x4(p, y, r, pos);
                // Verify matrix columns are orthonormal
                const Vec3 rgt = mat_right(m);
                const Vec3 up  = mat_up(m);
                const Vec3 bck = mat_back(m);
                assert(near_eq(length(rgt), 1.0f, 1e-4f));
                assert(near_eq(length(up),  1.0f, 1e-4f));
                assert(near_eq(length(bck), 1.0f, 1e-4f));
                assert(near_eq(dot(rgt, up),  0.0f, 1e-4f));
                assert(near_eq(dot(rgt, bck), 0.0f, 1e-4f));
                assert(near_eq(dot(up,  bck), 0.0f, 1e-4f));

                // Verify MW3 0x523BC0 Euler extraction recovers exact angles
                float out_p = 0.f, out_y = 0.f, out_r = 0.f;
                mat3x4_to_euler(m, out_p, out_y, out_r);
                assert(near_eq(p, out_p, 1e-4f));
                assert(near_eq(y, out_y, 1e-4f));
                assert(near_eq(r, out_r, 1e-4f));
                assert(near_eq(m[9],  pos.x, 1e-4f));
                assert(near_eq(m[10], pos.y, 1e-4f));
                assert(near_eq(m[11], pos.z, 1e-4f));
            }
        }
    }
}

static void test_cameras_and_spline() {
    FreeFlyCamera fcam{};
    const Mat3x4 start_m = euler_to_mat3x4(0.0f, 0.0f, 0.0f, Vec3{10.f, 20.f, 30.f});
    fcam.init_from_matrix(start_m, 60.0f);
    // At yaw=0, pitch=0, Back is (0, 0, 1), so Forward (-Back) is (0, 0, -1)
    fcam.step(1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f);
    assert(near_eq(fcam.pos.x, 10.0f, 1e-3f));
    assert(near_eq(fcam.pos.y, 20.0f, 1e-3f));
    assert(fcam.pos.z < 30.0f);

    OrbitCamera ocam{};
    ocam.init_from_pose(Vec3{100.f, 10.f, 200.f}, Vec3{100.f, 10.f, 230.f}, 55.0f);
    assert(near_eq(ocam.radius, 30.0f, 1e-3f));
    const Mat3x4 om = ocam.to_matrix();
    assert(near_eq(om[9], 100.0f, 1e-2f));
    assert(near_eq(om[10], 10.0f, 1e-2f));
    assert(near_eq(om[11], 230.0f, 1e-2f));

    DollySpline spline{};
    spline.add_keyframe(euler_to_mat3x4(0.0f, 0.0f, 0.0f, Vec3{0.f, 10.f, 0.f}), 60.0f, 2.0f);
    spline.add_keyframe(euler_to_mat3x4(0.2f, 1.0f, -0.1f, Vec3{100.f, 30.f, -50.f}), 40.0f, 2.0f);
    spline.add_keyframe(euler_to_mat3x4(-0.1f, 2.0f, 0.2f, Vec3{200.f, 20.f, -100.f}), 75.0f, 2.0f);
    assert(spline.keyframes.size() == 3);
    assert(near_eq(spline.duration_sec, 4.0f, 1e-4f));

    Mat3x4 eval_m{};
    float eval_fov = 0.0f;
    assert(spline.evaluate(1.0f, eval_m, eval_fov));
    assert(near_eq(eval_fov, 50.0f, 1e-3f));
    assert(eval_m[9] > 10.0f && eval_m[9] < 90.0f);
}

static void test_replay_ring_buffer_and_serialization() {
    // Simulate a 64 KB flat guest memory arena with 16 pages
    constexpr std::uint32_t kArenaSize = 16 * 4096;
    std::vector<std::uint8_t> guest_mem(kArenaSize, 0);
    std::vector<std::vector<std::uint8_t>> ground_truth_frames;

    PageDeltaReplayBuffer buf{};
    const std::vector<std::pair<std::uint32_t, std::uint32_t>> ranges = {{0x1000, 0x9000}};

    // Record 150 frames (spanning multiple 60-frame checkpoints)
    for (unsigned f = 0; f < 150; ++f) {
        // Mutate a few cachelines per frame
        const std::uint32_t offset1 = 0x1000 + ((f * 137) % 0x7F00);
        const std::uint32_t offset2 = 0x2000 + ((f * 293) % 0x6F00);
        guest_mem[offset1] = static_cast<std::uint8_t>((f * 31 + 7) & 0xFF);
        guest_mem[offset2] = static_cast<std::uint8_t>((f * 17 + 3) & 0xFF);

        ground_truth_frames.push_back(guest_mem);

        ReplayFrameRecord rec{};
        ReplayDeviceState dev{};
        dev.guest = 0x38000000;
        dev.viewport = 0x38000020;
        for (unsigned i = 0; i < dev.render_states.size(); ++i) dev.render_states[i] = f * 1000 + i;
        for (unsigned s = 0; s < 8; ++s) {
            for (unsigned i = 0; i < 32; ++i) dev.texture_states[s][i] = f * 1000 + s * 32 + i;
            dev.textures[s] = f * 8 + s;
        }
        rec.graphics_devices.push_back(dev);
        ReplayViewportState vp{dev.viewport, f, 1};
        for (unsigned i = 0; i < 11; ++i) vp.words[i] = f * 11 + i;
        rec.graphics_viewports.push_back(vp);
        rec.guest_tick_ms = f * 16;
        rec.mission_time_sec = float(f) / 60.0f;
        rec.dt_sec = 1.0f / 60.0f;
        rec.game_cam_mat = euler_to_mat3x4(0.0f, float(f) * 0.01f, 0.0f, Vec3{float(f), 5.0f, 0.0f});
        rec.game_cam_vfov_deg = 60.0f;
        buf.record_frame(guest_mem.data(), ranges, nullptr, std::move(rec), 120);
    }

    // Because max_frames = 120 and kCheckpointInterval = 60, trimming once leaves 90 frames (frames 60..149)
    assert(buf.frame_count() == 90);

    // Save to disk and reload into a fresh PageDeltaReplayBuffer
    const auto tmp_replay = (std::filesystem::temp_directory_path() / "mw3_unit_test.mw3replay").string();
    assert(buf.save_to_file(tmp_replay));

    PageDeltaReplayBuffer loaded{};
    assert(loaded.load_from_file(tmp_replay));
    assert(loaded.frame_count() == 90);

    // Test random-access seek & rewind across all 90 frames and measure latency
    const std::size_t test_indices[] = {89, 0, 45, 12, 77, 60, 59, 1, 88, 30};
    for (std::size_t idx : test_indices) {
        const auto t0 = std::chrono::steady_clock::now();
        assert(loaded.restore_frame(idx, guest_mem.data()));
        const auto elapsed_us = std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now() - t0).count();
        assert(elapsed_us < 5000); // Must be < 5 ms (5000 us)

        // Compare restored region [0x1000, 0x9000) with ground truth frame (idx + 60)
        const auto& truth = ground_truth_frames.at(idx + 60);
        assert(std::memcmp(guest_mem.data() + 0x1000, truth.data() + 0x1000, 0x8000) == 0);
        const auto& graphics = loaded.frame(idx);
        const unsigned source_frame = unsigned(idx + 60);
        assert(graphics.graphics_devices.size() == 1 && graphics.graphics_viewports.size() == 1);
        const auto& dev = graphics.graphics_devices[0];
        assert(dev.guest == 0x38000000 && dev.viewport == 0x38000020);
        for (unsigned i = 0; i < 256; ++i) assert(dev.render_states[i] == source_frame * 1000 + i);
        for (unsigned s = 0; s < 8; ++s) {
            for (unsigned i = 0; i < 32; ++i) assert(dev.texture_states[s][i] == source_frame * 1000 + s * 32 + i);
            assert(dev.textures[s] == source_frame * 8 + s);
        }
        const auto& vp = graphics.graphics_viewports[0];
        assert(vp.guest == dev.viewport && vp.background == source_frame && vp.set == 1);
        for (unsigned i = 0; i < 11; ++i) assert(vp.words[i] == source_frame * 11 + i);
    }

    // Version 2 has no provider-state payload and must not load as version 3.
    {
        std::fstream old(tmp_replay, std::ios::in | std::ios::out | std::ios::binary);
        old.seekp(7); old.put('2');
    }
    PageDeltaReplayBuffer incompatible;
    assert(!incompatible.load_from_file(tmp_replay));

    std::error_code ec;
    std::filesystem::remove(tmp_replay, ec);
}

static void test_png_and_overlay() {
    // 1. Test lossless PNG encoding
    const unsigned w = 320, h = 200;
    std::vector<std::uint8_t> rgb(w * h * 3, 0);
    for (unsigned y = 0; y < h; ++y) {
        for (unsigned x = 0; x < w; ++x) {
            rgb[(y * w + x) * 3 + 0] = static_cast<std::uint8_t>(x & 0xFF);
            rgb[(y * w + x) * 3 + 1] = static_cast<std::uint8_t>(y & 0xFF);
            rgb[(y * w + x) * 3 + 2] = 128;
        }
    }
    const auto png = encode_png_rgb24(rgb.data(), w, h);
    assert(png.size() > w * h * 3);
    const std::uint8_t expected_sig[8] = {137, 80, 78, 71, 13, 10, 26, 10};
    assert(std::memcmp(png.data(), expected_sig, 8) == 0);

    // 2. Test Overlay Render State
    OverlayRenderState st{};
    std::vector<std::uint32_t> canvas;
    // Live + Game Cam + no recording -> overlay does not draw
    assert(!render_overlay_canvas(st, w, h, canvas));

    // Photo Mode + FreeFly -> overlay draws legend
    st.mode = Mode::Photo;
    st.camera_mode = CameraMode::FreeFly;
    st.paused = true;
    assert(render_overlay_canvas(st, w, h, canvas));
    assert(canvas.size() == w * h);

    // F1 hides legend -> overlay does not draw
    st.show_legend = false;
    assert(!render_overlay_canvas(st, w, h, canvas));
}

int main() {
    test_euler_mat3x4_roundtrip();
    test_cameras_and_spline();
    test_replay_ring_buffer_and_serialization();
    test_png_and_overlay();
    std::printf("All Photo Mode & Replay Mode unit tests passed!\n");
    return 0;
}
