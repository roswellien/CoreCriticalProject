// Native Photo Mode (F11), Free/Orbit/Dolly Camera (C), Instant Replay Clip (F10), and Screenshot (F9).
// Included inside mw34::m4_crt_mfc_attach::Stage (mfc_stage.hpp).

#include <thread>
#include <mutex>
#include <condition_variable>
#include <deque>
#include <vector>
#include <algorithm>

inline std::string photo_replay_detect_encoder() {
    static std::string enc;
    if (!enc.empty()) return enc;
    // Check AMD AMF hardware encoder
    if (::system("ffmpeg -y -f lavfi -i testsrc=size=64x64:rate=30 -t 0.05 -c:v h264_amf -f null - >nul 2>&1") == 0) {
        enc = "h264_amf -quality speed -b:v 20M";
        return enc;
    }
    // Check NVIDIA NVENC hardware encoder
    if (::system("ffmpeg -y -f lavfi -i testsrc=size=64x64:rate=30 -t 0.05 -c:v h264_nvenc -f null - >nul 2>&1") == 0) {
        enc = "h264_nvenc -preset p1 -tune ll -b:v 20M";
        return enc;
    }
    // Fallback to CPU libx264 ultrafast zero-latency
    enc = "libx264 -preset ultrafast -tune zerolatency -crf 18";
    return enc;
}

struct AsyncVideoWriter {
    std::mutex mtx;
    std::condition_variable cv;
    std::thread worker;
    std::atomic<bool> active{false};
    std::atomic<bool> stop_signal{false};

    FILE* pipe{nullptr};
    std::deque<std::vector<std::uint8_t>> queue;
    std::vector<std::vector<std::uint8_t>> pool;
    unsigned width{0};
    unsigned height{0};
    std::atomic<unsigned> frames_written{0};
    std::string output_path;

    bool is_dvr{false};
    std::filesystem::path dvr_dir;

    void start(unsigned w, unsigned h, const std::string& pipe_cmd, const std::string& out_path, bool dvr = false, const std::filesystem::path& dvr_path = {}) {
        stop();
        width = w;
        height = h;
        output_path = out_path;
        frames_written = 0;
        is_dvr = dvr;
        dvr_dir = dvr_path;

        pipe = _popen(pipe_cmd.c_str(), "wb");
        if (!pipe) return;

        stop_signal = false;
        active = true;
        worker = std::thread([this]() {
            run_worker();
        });
    }

    void push_frame(const std::uint8_t* bgra, unsigned w, unsigned h) {
        if (!active || !pipe || w != width || h != height) return;
        const std::size_t bytes = std::size_t(w) * h * 4;

        std::vector<std::uint8_t> buf;
        {
            std::lock_guard<std::mutex> lk(mtx);
            // Drop frame if worker is congested (> 12 frames buffered, ~200ms) to ensure zero game lag
            if (queue.size() > 12) {
                return;
            }
            if (!pool.empty()) {
                buf = std::move(pool.back());
                pool.pop_back();
            }
        }
        if (buf.size() != bytes) buf.resize(bytes);
        std::memcpy(buf.data(), bgra, bytes);

        {
            std::lock_guard<std::mutex> lk(mtx);
            queue.push_back(std::move(buf));
        }
        cv.notify_one();
    }

    void stop() {
        if (!active) return;
        {
            std::lock_guard<std::mutex> lk(mtx);
            stop_signal = true;
        }
        cv.notify_all();
        if (worker.joinable()) {
            worker.join();
        }
        if (pipe) {
            _pclose(pipe);
            pipe = nullptr;
        }
        active = false;
        queue.clear();
        pool.clear();
    }

    void run_worker() {
        const std::size_t frame_bytes = std::size_t(width) * height * 4;
        while (true) {
            std::vector<std::uint8_t> frame;
            {
                std::unique_lock<std::mutex> lk(mtx);
                cv.wait(lk, [this]() { return !queue.empty() || stop_signal; });
                if (queue.empty() && stop_signal) break;
                if (!queue.empty()) {
                    frame = std::move(queue.front());
                    queue.pop_front();
                }
            }
            if (!frame.empty() && pipe) {
                std::fwrite(frame.data(), 1, frame_bytes, pipe);
                ++frames_written;
                {
                    std::lock_guard<std::mutex> lk(mtx);
                    if (pool.size() < 16) {
                        pool.push_back(std::move(frame));
                    }
                }
            }
        }
    }
};

struct PhotoReplayState {
    mw34::photo_replay::Mode mode{mw34::photo_replay::Mode::Live};
    mw34::photo_replay::CameraMode camera_mode{mw34::photo_replay::CameraMode::Game};
    bool paused{false};
    bool hide_hud{false};
    bool show_legend{true};
    float playback_speed{1.0f};
    float replay_playhead_sec{0.0f};
    std::size_t replay_cur_frame{0};
    float replay_subframe_alpha{0.0f};

    mw34::photo_replay::FreeFlyCamera free_cam{};
    mw34::photo_replay::OrbitCamera orbit_cam{};
    mw34::photo_replay::DollySpline dolly_cam{};
    mw34::photo_replay::PageDeltaReplayBuffer replay_buf{};

    mw34::photo_replay::Mat3x4 last_world_cam_mat{mw34::photo_replay::identity_mat3x4()};
    float last_world_cam_vfov_deg{60.0f};
    bool has_world_cam{false};

    std::size_t orbit_target_idx{0};
    std::vector<mw34::photo_replay::OrbitTargetSample> current_orbit_targets;
    std::set<std::uint32_t> tracked_node_datas;

    bool screenshot_requested{false};
    bool video_recording{false};
    AsyncVideoWriter video_pipeline{};

    bool dvr_enabled{true};
    bool dvr_checked{false};
    AsyncVideoWriter dvr_pipeline{};

    std::string status_banner;
    std::chrono::steady_clock::time_point status_until{};
    std::chrono::steady_clock::time_point suppress_escape_until{};
    std::chrono::steady_clock::time_point last_poll_time{};
    bool poll_time_init{false};
    POINT last_mouse_pt{};
    bool mouse_init{false};
    float accum_di_dx{0.0f};
    float accum_di_dy{0.0f};
    float accum_di_dz{0.0f};
    std::array<bool, 256> prev_keys{};

    unsigned suppress_d3d_depth{0};
    bool write_watch_checked{false};
    bool write_watch_ok{false};
    bool cli_checked{false};

    bool has_saved_player_cam{false};
    unsigned saved_cam_ctrl{0};
    unsigned saved_cam_mode_id{1};
    unsigned saved_cam_prev_id{1};
    unsigned saved_cam_flags{0};
    unsigned saved_player_root{0};
    unsigned saved_player_root_flags{0};
    mw34::photo_replay::Mat3x4 saved_live_cam_mat{mw34::photo_replay::identity_mat3x4()};
    float saved_live_cam_vfov_deg{60.0f};

    bool has_saved_frustum{false};
    unsigned saved_frustum_node{0};
    unsigned saved_frustum_data{0};
    unsigned saved_cam_h{0};
    unsigned saved_cam_v{0};
    unsigned saved_cam_half_h{0};
    unsigned saved_cam_half_v{0};
    unsigned saved_cam_cot_h{0};
    unsigned saved_cam_cot_v{0};
    WideCamera saved_wc{};
    bool has_saved_wc{false};

    ~PhotoReplayState() {
        video_pipeline.stop();
        dvr_pipeline.stop();
    }
};

PhotoReplayState photo_replay{};

void photo_replay_set_status(const std::string& msg, int duration_ms = 3500) {
    photo_replay.status_banner = msg;
    photo_replay.status_until = std::chrono::steady_clock::now() + std::chrono::milliseconds(duration_ms);
}

std::filesystem::path photo_replay_root_dir() {
    if (const char* env_dir = std::getenv("MW34_PHOTO_REPLAY_DIR"); env_dir && *env_dir) {
        return std::filesystem::path(env_dir);
    }
    const auto exe = host.paths.find(0x400000U);
    if (exe != host.paths.end()) {
        std::error_code ec;
        auto p = std::filesystem::absolute(exe->second, ec).parent_path();
        for (int i = 0; i < 4; ++i) {
            if (std::filesystem::exists(p / "AGENTS.md", ec) || std::filesystem::exists(p / "local", ec)) {
                return p / "local";
            }
            if (!p.has_parent_path()) break;
            p = p.parent_path();
        }
    }
    return std::filesystem::current_path() / "local";
}

std::string photo_replay_timestamp_str(bool with_ms = true) {
    SYSTEMTIME st{};
    ::GetLocalTime(&st);
    char buf[64]{};
    if (with_ms) {
        std::snprintf(buf, sizeof(buf), "%04u%02u%02u_%02u%02u%02u_%03u",
                      unsigned(st.wYear), unsigned(st.wMonth), unsigned(st.wDay),
                      unsigned(st.wHour), unsigned(st.wMinute), unsigned(st.wSecond),
                      unsigned(st.wMilliseconds));
    } else {
        std::snprintf(buf, sizeof(buf), "%04u%02u%02u_%02u%02u%02u",
                      unsigned(st.wYear), unsigned(st.wMonth), unsigned(st.wDay),
                      unsigned(st.wHour), unsigned(st.wMinute), unsigned(st.wSecond));
    }
    return buf;
}

bool photo_replay_detached_cam() const noexcept {
    return photo_replay.camera_mode != mw34::photo_replay::CameraMode::Game;
}

bool photo_replay_sim_frozen() const noexcept {
    return photo_replay.mode == mw34::photo_replay::Mode::Photo ||
           photo_replay.mode == mw34::photo_replay::Mode::Replay;
}

bool photo_replay_consume_input() const noexcept {
    return photo_replay.mode != mw34::photo_replay::Mode::Live ||
           photo_replay.camera_mode != mw34::photo_replay::CameraMode::Game;
}

bool photo_replay_hide_hud() const noexcept {
    return photo_replay.hide_hud;
}

bool photo_replay_suppress_d3d_draw(unsigned hud_role) const noexcept {
    // 0x57E110 flushes shared translucent geometry, including world water.
    // Hide only authenticated HUD draws, never the world transparency pass.
    return photo_replay.hide_hud && photo_replay.suppress_d3d_depth > 0 && hud_role != WideWorld;
}

void photo_replay_filter_device_state(unsigned z, unsigned char* b) {
    if (!b) return;
    if (photo_replay_consume_input()) {
        if (z == sizeof(DIMOUSESTATE)) {
            DIMOUSESTATE ms{};
            std::memcpy(&ms, b, sizeof(ms));
            photo_replay.accum_di_dx += float(ms.lX);
            photo_replay.accum_di_dy += float(ms.lY);
            photo_replay.accum_di_dz += float(ms.lZ);
        }
        std::memset(b, 0, z);
        return;
    }
    if (z == 256) {
        // Suppress hotkeys so MW3 game engine never receives them:
        // DIK_F9 (0x43): Screenshot / Shift+F9 Video
        // DIK_F10 (0x44): Instant Replay Clip
        // DIK_F11 (0x57): Photo Mode / Free Cam
        // DIK_F12 (0x58): Reserved
        b[0x43] = 0;
        b[0x44] = 0;
        b[0x57] = 0;
        b[0x58] = 0;
        if (std::chrono::steady_clock::now() < photo_replay.suppress_escape_until) {
            b[1] = 0; // Suppress DIK_ESCAPE (0x01) so exiting Photo/Replay via ESC does not trigger Abort Mission
        }
    }
}

void photo_replay_filter_device_data(DIDEVICEOBJECTDATA_DX3* b, DWORD& cnt) {
    if (photo_replay_consume_input()) {
        cnt = 0;
        return;
    }
    if (b && cnt > 0) {
        const bool suppress_esc = std::chrono::steady_clock::now() < photo_replay.suppress_escape_until;
        DWORD out_k = 0;
        for (DWORD k = 0; k < cnt; ++k) {
            const DWORD ofs = b[k].dwOfs;
            if (ofs == 0x43 || ofs == 0x44 || ofs == 0x57 || ofs == 0x58) continue;
            if (suppress_esc && ofs == 1) continue;
            if (out_k != k) b[out_k] = b[k];
            ++out_k;
        }
        cnt = out_k;
    }
}

void photo_replay_flush_di_keyboard() {
    for (const auto& [g_dev, fmt_sz] : host.di_format) {
        if (fmt_sz == 256) {
            if (auto* co = host.com_object(g_dev); co && co->native) {
                auto* dv = reinterpret_cast<IDirectInputDeviceA*>(co->native);
                DWORD items = INFINITE;
                dv->GetDeviceData(sizeof(DIDEVICEOBJECTDATA_DX3), nullptr, &items, 0);
            }
        }
    }
}

mw34::photo_replay::Mat3x4 photo_replay_read_mat3x4(unsigned addr) {
    mw34::photo_replay::Mat3x4 m{};
    for (unsigned i = 0; i < 12; ++i) {
        const unsigned bits = load(addr + 4 * i);
        float f = 0.0f;
        std::memcpy(&f, &bits, 4);
        m[i] = std::isfinite(f) ? f : 0.0f;
    }
    return m;
}

void photo_replay_write_mat3x4(unsigned addr, const mw34::photo_replay::Mat3x4& m) {
    for (unsigned i = 0; i < 12; ++i) {
        const float f = std::isfinite(m[i]) ? m[i] : 0.0f;
        unsigned bits = 0;
        std::memcpy(&bits, &f, 4);
        store(addr + 4 * i, bits);
    }
}

unsigned photo_replay_player_root_node() {
    if (readable(0x60861c, 4)) {
        const unsigned c = load(0x60861c);
        if (c && readable(c + 0x14, 4)) {
            const unsigned actor = load(c + 0x14);
            if (actor && readable(actor + 0x04, 4)) {
                const unsigned root = load(actor + 0x04);
                if (root && readable(root, 0x3c)) return root;
            }
        }
    }
    if (readable(0x63d8d4, 4)) {
        const unsigned u = load(0x63d8d4);
        if (u && readable(u + 0x04, 4)) {
            const unsigned root = load(u + 0x04);
            if (root && readable(root, 0x3c)) return root;
        }
    }
    return 0;
}

bool photo_replay_read_node_world_pos(unsigned node_va, mw34::photo_replay::Vec3& out_pos) {
    if (!node_va || !readable(node_va, 0x3c)) return false;
    const unsigned data = load(node_va + 0x38);
    if (!data || !readable(data, 0x90)) return false;
    // Prefer cached world Mat3x4 at data + 0x60; fall back to local Mat3x4 at data + 0x30
    auto m = photo_replay_read_mat3x4(data + 0x60);
    if (std::fabs(m[9]) < 1e-3f && std::fabs(m[10]) < 1e-3f && std::fabs(m[11]) < 1e-3f) {
        m = photo_replay_read_mat3x4(data + 0x30);
    }
    if (!std::isfinite(m[9]) || !std::isfinite(m[10]) || !std::isfinite(m[11])) return false;
    if (std::fabs(m[9]) < 1e-3f && std::fabs(m[11]) < 1e-3f) return false;
    out_pos = {m[9], m[10] + 5.5f, m[11]};
    return true;
}

void photo_replay_collect_orbit_targets(std::vector<mw34::photo_replay::OrbitTargetSample>& out) {
    out.clear();
    std::set<std::uint32_t> seen_roots;

    auto try_add_root = [&](std::uint32_t root_va, const char* default_label) {
        if (!root_va || seen_roots.count(root_va)) return;
        mw34::photo_replay::Vec3 pos{};
        if (!photo_replay_read_node_world_pos(root_va, pos)) return;

        seen_roots.insert(root_va);
        mw34::photo_replay::OrbitTargetSample samp{};
        samp.root_va = root_va;
        samp.pos = pos;
        std::string nm = pose_name(root_va, 23);
        if (default_label) {
            std::snprintf(samp.label, sizeof(samp.label), "%s", default_label);
        } else if (!nm.empty()) {
            std::snprintf(samp.label, sizeof(samp.label), "%s", nm.c_str());
        } else {
            std::snprintf(samp.label, sizeof(samp.label), "UNIT");
        }
        out.push_back(samp);
    };

    // 1. Always place Player Mech first if present
    const unsigned player_root = photo_replay_player_root_node();
    if (player_root) {
        try_add_root(player_root, "PLAYER MECH");
    }

    // 2. Discover all Mechs via "hip" nodes (parent of "hip" is the Mech root assembly)
    unsigned mech_idx = 1;
    for (std::uint32_t data_va : photo_replay.tracked_node_datas) {
        if (!readable(data_va, 0x60)) continue;
        const unsigned owner_node = load(data_va);
        if (!owner_node || !readable(owner_node, 0x5c)) continue;
        if (pose_name(owner_node, 20) == "hip") {
            const unsigned parent_root = override_parent(owner_node);
            const unsigned target_root = parent_root ? parent_root : owner_node;
            if (seen_roots.count(target_root)) continue;
            char lbl[24]{};
            if (out.empty() && !player_root) {
                std::snprintf(lbl, sizeof(lbl), "PLAYER MECH");
            } else {
                std::snprintf(lbl, sizeof(lbl), "MECH #%u", ++mech_idx);
            }
            try_add_root(target_root, lbl);
        }
    }

    // 3. Scan top-level vehicle/object assemblies under the world root
    const unsigned world_ctx = readable(0x5f4c8c, 4) ? load(0x5f4c8c) : 0;
    const unsigned world_root = (world_ctx && readable(world_ctx, 4)) ? load(world_ctx) : 0;
    if (world_root) {
        unsigned unit_idx = 1;
        for (std::uint32_t data_va : photo_replay.tracked_node_datas) {
            if (!readable(data_va, 0x60)) continue;
            const unsigned owner_node = load(data_va);
            if (!owner_node || !readable(owner_node, 0x5c)) continue;
            if (override_parent(owner_node) != world_root) continue;
            const unsigned ntype = load(owner_node + 0x34);
            if (ntype != 4 && ntype != 5) continue;
            const std::string nm = pose_name(owner_node, 20);
            if (nm == "labcam" || nm == "zoomcam" || nm == "camx") continue;
            char lbl[24]{};
            if (!nm.empty()) {
                std::snprintf(lbl, sizeof(lbl), "UNIT %u (%s)", unit_idx++, nm.c_str());
            } else {
                std::snprintf(lbl, sizeof(lbl), "UNIT %u", unit_idx++);
            }
            try_add_root(owner_node, lbl);
            if (out.size() >= 32) break;
        }
    }
}

mw34::photo_replay::Mat3x4 photo_replay_active_camera_mat(float& out_fov_deg) {
    using namespace mw34::photo_replay;
    if (photo_replay.camera_mode == CameraMode::FreeFly) {
        out_fov_deg = photo_replay.free_cam.fov_deg;
        return photo_replay.free_cam.to_matrix();
    }
    if (photo_replay.camera_mode == CameraMode::Orbit) {
        if (!photo_replay.current_orbit_targets.empty()) {
            const std::size_t idx = photo_replay.orbit_target_idx % photo_replay.current_orbit_targets.size();
            Vec3 live_pos = photo_replay.current_orbit_targets[idx].pos;
            if (photo_replay.current_orbit_targets[idx].root_va) {
                photo_replay_read_node_world_pos(photo_replay.current_orbit_targets[idx].root_va, live_pos);
                photo_replay.current_orbit_targets[idx].pos = live_pos;
            }
            photo_replay.orbit_cam.target_center = live_pos;
        }
        out_fov_deg = photo_replay.orbit_cam.fov_deg;
        return photo_replay.orbit_cam.to_matrix();
    }
    if (photo_replay.camera_mode == CameraMode::Dolly) {
        Mat3x4 m{};
        float fov = photo_replay.free_cam.fov_deg;
        if (photo_replay.dolly_cam.evaluate(photo_replay.dolly_cam.playhead_sec, m, fov)) {
            out_fov_deg = fov;
            return m;
        }
        out_fov_deg = photo_replay.free_cam.fov_deg;
        return photo_replay.free_cam.to_matrix();
    }
    // CameraMode::Game
    if (photo_replay.mode == Mode::Replay && !photo_replay.replay_buf.empty()) {
        const std::size_t f0 = std::min(photo_replay.replay_cur_frame, photo_replay.replay_buf.frame_count() - 1);
        const auto& rec0 = photo_replay.replay_buf.frame(f0);
        if (photo_replay.replay_subframe_alpha > 1e-3f && f0 + 1 < photo_replay.replay_buf.frame_count()) {
            const auto& rec1 = photo_replay.replay_buf.frame(f0 + 1);
            out_fov_deg = rec0.game_cam_vfov_deg + (rec1.game_cam_vfov_deg - rec0.game_cam_vfov_deg) * photo_replay.replay_subframe_alpha;
            return interpolate_mat3x4(rec0.game_cam_mat, rec1.game_cam_mat, photo_replay.replay_subframe_alpha);
        }
        out_fov_deg = rec0.game_cam_vfov_deg;
        return rec0.game_cam_mat;
    }
    out_fov_deg = photo_replay.last_world_cam_vfov_deg;
    return photo_replay.last_world_cam_mat;
}

void photo_replay_save_player_cam_state() {
    photo_replay.saved_live_cam_mat = photo_replay.last_world_cam_mat;
    photo_replay.saved_live_cam_vfov_deg = photo_replay.last_world_cam_vfov_deg;
    photo_replay.has_saved_player_cam = false;
    if (readable(0x5f4c8c, 8)) {
        const unsigned world_ctx = load(0x5f4c8c);
        if (world_ctx && readable(world_ctx + 0x58, 8)) {
            const unsigned ctrl = load(world_ctx + 0x58);
            photo_replay.saved_cam_ctrl = ctrl;
            photo_replay.saved_cam_prev_id = load(world_ctx + 0x5c);
            if (ctrl && readable(ctrl + 0x04, 4)) {
                photo_replay.saved_cam_mode_id = load(ctrl + 0x04);
                photo_replay.has_saved_player_cam = true;
            }
        }
        const unsigned cam_node = (world_ctx && readable(world_ctx + 4, 4)) ? load(world_ctx + 4) : 0;
        const unsigned cam_data = (cam_node && readable(cam_node + 0x38, 4)) ? load(cam_node + 0x38) : 0;
        if (cam_data && readable(cam_data, 0x1dc)) {
            photo_replay.saved_frustum_node = cam_node;
            photo_replay.saved_frustum_data = cam_data;
            photo_replay.saved_cam_h = load(cam_data + 0xe8);
            photo_replay.saved_cam_v = load(cam_data + 0xec);
            photo_replay.saved_cam_half_h = load(cam_data + 0xf0);
            photo_replay.saved_cam_half_v = load(cam_data + 0xf4);
            photo_replay.saved_cam_cot_h = load(cam_data + 0x1d4);
            photo_replay.saved_cam_cot_v = load(cam_data + 0x1d8);
            auto it = wide_cameras.find(cam_data);
            if (it != wide_cameras.end()) {
                photo_replay.saved_wc = it->second;
                photo_replay.has_saved_wc = true;
            } else {
                photo_replay.has_saved_wc = false;
            }
            photo_replay.has_saved_frustum = true;
        }
    }
    if (readable(0x5f4d04, 4)) {
        const unsigned fp = load(0x5f4d04);
        if (fp && readable(fp, 4)) {
            photo_replay.saved_cam_flags = load(fp);
        }
    }
    const unsigned proot = photo_replay_player_root_node();
    photo_replay.saved_player_root = proot;
    if (proot && readable(proot + 0x24, 4)) {
        photo_replay.saved_player_root_flags = load(proot + 0x24);
    }
}

void photo_replay_restore_player_cam_state() {
    photo_replay.last_world_cam_mat = photo_replay.saved_live_cam_mat;
    photo_replay.last_world_cam_vfov_deg = photo_replay.saved_live_cam_vfov_deg;

    if (photo_replay.has_saved_frustum) {
        const unsigned cdata = photo_replay.saved_frustum_data;
        if (cdata && writable(cdata, 0x1dc)) {
            store(cdata + 0xe8, photo_replay.saved_cam_h);
            store(cdata + 0xec, photo_replay.saved_cam_v);
            store(cdata + 0xf0, photo_replay.saved_cam_half_h);
            store(cdata + 0xf4, photo_replay.saved_cam_half_v);
            store(cdata + 0x1d4, photo_replay.saved_cam_cot_h);
            store(cdata + 0x1d8, photo_replay.saved_cam_cot_v);
            store(cdata + 0xf8, 1);
            store(cdata + 0x138, 1);
            // Type-1 camera data is not a type-5 transform block. The original
            // camera builder restores its pose from the untouched node hierarchy.
            if (writable(cdata + 0x1e0, 4)) {
                store(cdata + 0x1e0, 0); // Force spatial sector update
            }
            if (photo_replay.has_saved_wc) {
                wide_cameras[cdata] = photo_replay.saved_wc;
            } else {
                wide_cameras.erase(cdata);
            }
        }
        photo_replay.has_saved_frustum = false;
    }

    if (!photo_replay.has_saved_player_cam) return;
    if (readable(0x5f4c8c, 4)) {
        const unsigned world_ctx = load(0x5f4c8c);
        if (world_ctx && writable(world_ctx + 0x58, 8)) {
            if (photo_replay.saved_cam_ctrl) {
                store(world_ctx + 0x58, photo_replay.saved_cam_ctrl);
                if (writable(photo_replay.saved_cam_ctrl + 0x04, 4)) {
                    store(photo_replay.saved_cam_ctrl + 0x04, photo_replay.saved_cam_mode_id);
                }
            }
            store(world_ctx + 0x5c, photo_replay.saved_cam_prev_id);
        }
    }
    if (readable(0x5f4d04, 4)) {
        const unsigned fp = load(0x5f4d04);
        if (fp && writable(fp, 4)) {
            store(fp, photo_replay.saved_cam_flags);
        }
    }
    const unsigned proot = photo_replay.saved_player_root ? photo_replay.saved_player_root : photo_replay_player_root_node();
    if (proot && writable(proot + 0x24, 4)) {
        if (photo_replay.saved_cam_mode_id == 1) {
            // Cockpit view: ensure external 3D Mech visibility flag (bit 0x04) is cleared
            store(proot + 0x24, load(proot + 0x24) & ~0x4U);
        } else {
            store(proot + 0x24, photo_replay.saved_player_root_flags);
        }
    }
    photo_replay.has_saved_player_cam = false;
}

void photo_replay_init_detached_camera(mw34::photo_replay::CameraMode target_mode) {
    using namespace mw34::photo_replay;
    if (target_mode == CameraMode::Game) {
        photo_replay_restore_player_cam_state();
        photo_replay.camera_mode = CameraMode::Game;
        return;
    }
    if (photo_replay.camera_mode == CameraMode::Game && !photo_replay.has_saved_frustum) {
        photo_replay_save_player_cam_state();
    }
    float cur_fov = photo_replay.last_world_cam_vfov_deg;
    const Mat3x4 cur_mat = (photo_replay.camera_mode == CameraMode::Game)
        ? photo_replay.last_world_cam_mat
        : photo_replay_active_camera_mat(cur_fov);

    photo_replay_collect_orbit_targets(photo_replay.current_orbit_targets);
    if (target_mode == CameraMode::FreeFly) {
        photo_replay.free_cam.init_from_matrix(cur_mat, cur_fov);
        // Preserve the current framing on entry; moving the camera is explicit.
    } else if (target_mode == CameraMode::Orbit) {
        Vec3 pivot = mat_pos(cur_mat) + mat_forward(cur_mat) * 24.0f;
        if (!photo_replay.current_orbit_targets.empty()) {
            photo_replay.orbit_target_idx %= photo_replay.current_orbit_targets.size();
            pivot = photo_replay.current_orbit_targets[photo_replay.orbit_target_idx].pos;
        }
        float pitch_r = 0.0f, yaw_r = 0.0f, roll_r = 0.0f;
        mat3x4_to_euler(cur_mat, pitch_r, yaw_r, roll_r);
        photo_replay.orbit_cam.init_from_pose(pivot, mat_pos(cur_mat), cur_fov, yaw_r);
    } else if (target_mode == CameraMode::Dolly) {
        photo_replay.free_cam.init_from_matrix(cur_mat, cur_fov);
    }
    photo_replay.camera_mode = target_mode;
}

void photo_replay_record_live_snapshot() {
    if (frontend_on() || photo_replay.mode != mw34::photo_replay::Mode::Live) return;
    auto* flat = reinterpret_cast<std::uint8_t*>(runtime.memory().flat_base());
    if (!flat) return;

    mw34::vkscene::HostFpEnvironment fp;
    using namespace mw34::photo_replay;

    ReplayFrameRecord rec{};
    rec.guest_tick_ms = host.guest_tick();
    rec.mission_time_sec = readable(0x72c528, 4) ? wide_float(0x72c528) : (float(host.frames) / 60.0f);
    rec.dt_sec = readable(0x72c52c, 4) ? wide_float(0x72c52c) : (1.0f / 60.0f);
    rec.game_cam_mat = photo_replay.last_world_cam_mat;
    rec.game_cam_vfov_deg = photo_replay.last_world_cam_vfov_deg;

    rec.gheap_top = host.gheap.top;
    rec.gheap_mapped = host.gheap.mapped;
    rec.gheap_region_end = host.gheap.region_end;
    rec.gheap_allocs = host.gheap.allocs;
    rec.gheap_frees = host.gheap.frees;
    rec.gheap_free_blocks.assign(host.gheap.free_blocks.begin(), host.gheap.free_blocks.end());
    rec.gheap_live.assign(host.gheap.live.begin(), host.gheap.live.end());
    rec.gheap_regions.assign(host.gheap.regions.begin(), host.gheap.regions.end());
    rec.gheap_region_owners.assign(host.gheap.region_owners.begin(), host.gheap.region_owners.end());

    // Guest render-state caches and the host device must describe the same frame.
    // Commands, scene ownership and Vulkan resources stay with the live renderer.
    for (const auto& d : host.devices) if (host.com_object(d.guest)) {
        rec.graphics_devices.push_back({d.guest, d.current, d.rs, d.tss, d.textures});
    }
    for (const auto& v : host.viewports) if (host.com_object(v.guest)) {
        mw34::photo_replay::ReplayViewportState saved{v.guest, v.background, unsigned(v.set)};
        std::memcpy(saved.words.data(), v.vp.data(), v.vp.size());
        rec.graphics_viewports.push_back(saved);
    }
    if (rec.graphics_devices.size() > 64 || rec.graphics_viewports.size() > 256)
        throw std::runtime_error("Replay graphics state exceeds the supported device/viewport count");

    // Capture current node transforms for smooth sub-frame slow-motion interpolation
    rec.node_poses.reserve(photo_replay.tracked_node_datas.size());
    for (std::uint32_t data_va : photo_replay.tracked_node_datas) {
        if (readable(data_va + 0x30, 48)) {
            rec.node_poses.push_back({data_va, photo_replay_read_mat3x4(data_va + 0x30)});
        }
    }

    photo_replay_collect_orbit_targets(rec.orbit_targets);
    photo_replay.current_orbit_targets = rec.orbit_targets;

    std::vector<std::pair<std::uint32_t, std::uint32_t>> ranges;
    ranges.push_back({game_data, game_data_end});
    for (const auto& [r_lo, r_hi] : host.gheap.regions) {
        const std::uint32_t end_va = std::min<std::uint32_t>(r_hi, std::max<std::uint32_t>(r_lo + 4096U, (host.gheap.top + 4095U) & ~4095U));
        if (end_va > r_lo) ranges.push_back({r_lo, end_va});
    }

    std::vector<std::uint32_t> dirty_pages;
    bool use_dirty_hint = false;
    if (!photo_replay.write_watch_checked) {
        photo_replay.write_watch_checked = true;
        std::array<void*, 64> addrs{};
        ULONG_PTR cnt = addrs.size();
        DWORD gran = 0;
        photo_replay.write_watch_ok = (::GetWriteWatch(0, flat + game_data, 4096, addrs.data(), &cnt, &gran) == 0);
    }
    if (photo_replay.write_watch_ok && !photo_replay.replay_buf.empty()) {
        use_dirty_hint = true;
        std::vector<void*> addrs(16384);
        for (const auto& [r_lo, r_hi] : ranges) {
            ULONG_PTR cnt = addrs.size();
            DWORD gran = 0;
            if (::GetWriteWatch(WRITE_WATCH_FLAG_RESET, flat + r_lo, r_hi - r_lo, addrs.data(), &cnt, &gran) == 0) {
                if (cnt == addrs.size()) {
                    // Buffer saturated; fall back to full scan for this frame
                    use_dirty_hint = false;
                    break;
                }
                for (ULONG_PTR i = 0; i < cnt; ++i) {
                    const auto off = static_cast<std::uint32_t>(static_cast<const std::uint8_t*>(addrs[i]) - flat);
                    dirty_pages.push_back(off & ~4095U);
                }
            } else {
                use_dirty_hint = false;
                break;
            }
        }
    }

    photo_replay.replay_buf.record_frame(flat, ranges, use_dirty_hint ? &dirty_pages : nullptr, std::move(rec));
    photo_replay.replay_cur_frame = photo_replay.replay_buf.frame_count() - 1;
    photo_replay.replay_playhead_sec = photo_replay.replay_buf.total_duration_sec();
}

void photo_replay_restore_snapshot(std::size_t frame_idx, float subframe_alpha) {
    if (photo_replay.replay_buf.empty()) return;
    auto* flat = reinterpret_cast<std::uint8_t*>(runtime.memory().flat_base());
    if (!flat) return;

    mw34::vkscene::HostFpEnvironment fp;
    frame_idx = std::min(frame_idx, photo_replay.replay_buf.frame_count() - 1);
    const auto& rec = photo_replay.replay_buf.frame(frame_idx);

    // Ensure all guest heap regions present in the snapshot are mapped
    for (const auto& [r_lo, r_hi] : rec.gheap_regions) {
        if (!host.gheap.regions.count(r_lo)) {
            try {
                runtime.memory().map({r_lo}, r_hi - r_lo, Permissions::read | Permissions::write);
                host.gheap.regions[r_lo] = r_hi;
            } catch (...) {}
        }
    }

    photo_replay.replay_buf.restore_frame(frame_idx, flat);

    for (const auto& saved : rec.graphics_viewports) {
        auto* v = viewport(saved.guest);
        if (!v || !host.com_object(saved.guest))
            throw std::runtime_error("Replay viewport is no longer live in this session");
        std::memcpy(v->vp.data(), saved.words.data(), v->vp.size());
        v->background = saved.background;
        v->set = saved.set != 0;
    }
    for (const auto& saved : rec.graphics_devices) {
        auto* d = device(saved.guest);
        if (!d || !host.com_object(saved.guest))
            throw std::runtime_error("Replay graphics device is no longer live in this session");
        if (saved.viewport && (!viewport(saved.viewport) ||
            std::find(d->viewports.begin(), d->viewports.end(), saved.viewport) == d->viewports.end()))
            throw std::runtime_error("Replay viewport does not belong to its graphics device");
        d->rs = saved.render_states;
        d->tss = saved.texture_states;
        d->textures = saved.textures;
        d->current = saved.viewport;
        ++d->epoch;
        d->snap.reset();
        d->snap_epoch = 0;
    }

    // Synchronize host gheap metadata with the restored snapshot
    host.gheap.top = rec.gheap_top;
    host.gheap.mapped = std::max(host.gheap.mapped, rec.gheap_mapped);
    host.gheap.region_end = rec.gheap_region_end;
    host.gheap.allocs = rec.gheap_allocs;
    host.gheap.frees = rec.gheap_frees;
    for (const auto& kv : rec.gheap_region_owners) {
        const auto [it, added] = host.gheap.region_owners.emplace(kv.first, kv.second);
        if (!added && it->second != kv.second) throw std::runtime_error("Replay heap ownership differs from this session");
    }
    host.gheap.free_blocks.clear();
    for (const auto& kv : rec.gheap_free_blocks) host.gheap.free_blocks.emplace(kv.first, kv.second);
    host.gheap.live.clear();
    for (const auto& kv : rec.gheap_live) host.gheap.live.emplace(kv.first, kv.second);

    photo_replay.current_orbit_targets = rec.orbit_targets;

    // Apply sub-frame skeletal/node pose interpolation when playing in slow motion
    if (subframe_alpha > 1e-3f && frame_idx + 1 < photo_replay.replay_buf.frame_count()) {
        const auto& next_rec = photo_replay.replay_buf.frame(frame_idx + 1);
        std::unordered_map<std::uint32_t, const mw34::photo_replay::Mat3x4*> next_map;
        next_map.reserve(next_rec.node_poses.size());
        for (const auto& np : next_rec.node_poses) next_map.emplace(np.data_va, &np.mat);

        for (const auto& cur_np : rec.node_poses) {
            auto it = next_map.find(cur_np.data_va);
            if (it != next_map.end() && writable(cur_np.data_va + 0x30, 48)) {
                const auto interp = mw34::photo_replay::interpolate_mat3x4(cur_np.mat, *it->second, subframe_alpha);
                photo_replay_write_mat3x4(cur_np.data_va + 0x30, interp);
            }
        }
    }
}

void photo_replay_stop_video() {
    if (!photo_replay.video_pipeline.active) return;
    const std::string path = photo_replay.video_pipeline.output_path;
    const unsigned frames = photo_replay.video_pipeline.frames_written;
    photo_replay.video_pipeline.stop();
    photo_replay.video_recording = false;
    photo_replay_set_status("SAVED VIDEO (" + std::to_string(frames) + " FRAMES): " + std::filesystem::path(path).filename().string(), 5000);
}

void photo_replay_start_video(unsigned w, unsigned h) {
    if (photo_replay.video_pipeline.active) {
        photo_replay_stop_video();
        return;
    }
    std::error_code ec;
    const auto vid_dir = photo_replay_root_dir() / "videos";
    std::filesystem::create_directories(vid_dir, ec);
    const std::string stamp = photo_replay_timestamp_str(false);
    const auto mp4_path = vid_dir / ("mw3_take_" + stamp + ".mp4");

    const std::string encoder = photo_replay_detect_encoder();
    char cmd[2048]{};
    std::snprintf(cmd, sizeof(cmd),
                  "ffmpeg -y -f rawvideo -pixel_format bgra -video_size %ux%u -framerate 60 -i - "
                  "-c:v %s -pix_fmt yuv420p \"%s\" >nul 2>&1",
                  w, h, encoder.c_str(), mp4_path.string().c_str());

    photo_replay.video_pipeline.start(w, h, cmd, mp4_path.string());
    photo_replay.video_recording = photo_replay.video_pipeline.active;
    if (photo_replay.video_recording) {
        photo_replay_set_status("RECORDING 60FPS VIDEO (SHIFT+F9 TO STOP)", 3000);
    } else {
        photo_replay_set_status("FAILED TO START VIDEO RECORDING", 3500);
    }
}

void photo_replay_start_dvr(unsigned w, unsigned h) {
    if (photo_replay.dvr_pipeline.active || frontend_on()) return;
    std::error_code ec;
    const auto dvr_dir = photo_replay_root_dir() / "replays" / ".temp_dvr";
    std::filesystem::create_directories(dvr_dir, ec);

    const std::string encoder = photo_replay_detect_encoder();
    char cmd[2048]{};
    const auto seg_pattern = dvr_dir / "seg_%02d.mp4";
    std::snprintf(cmd, sizeof(cmd),
                  "ffmpeg -y -f rawvideo -pixel_format bgra -video_size %ux%u -framerate 60 -i - "
                  "-c:v %s -pix_fmt yuv420p -f segment -segment_time 10 -segment_wrap 7 -reset_timestamps 1 \"%s\" >nul 2>&1",
                  w, h, encoder.c_str(), seg_pattern.string().c_str());

    photo_replay.dvr_pipeline.start(w, h, cmd, dvr_dir.string(), true, dvr_dir);
}

void photo_replay_stop_dvr() {
    if (!photo_replay.dvr_pipeline.active) return;
    photo_replay.dvr_pipeline.stop();
}

void photo_replay_save_instant_replay_clip() {
    const auto rep_dir = photo_replay_root_dir() / "replays";
    const auto dvr_dir = rep_dir / ".temp_dvr";
    std::error_code ec;

    if (!std::filesystem::exists(dvr_dir, ec)) {
        photo_replay_set_status("INSTANT REPLAY BUFFER NOT READY", 3000);
        return;
    }

    // Collect all valid segments in .temp_dvr
    struct SegInfo {
        std::filesystem::path path;
        std::filesystem::file_time_type mtime;
    };
    std::vector<SegInfo> segs;
    for (const auto& entry : std::filesystem::directory_iterator(dvr_dir, ec)) {
        if (entry.path().extension() == ".mp4") {
            const auto sz = entry.file_size(ec);
            if (sz > 1024) {
                segs.push_back({entry.path(), entry.last_write_time(ec)});
            }
        }
    }

    if (segs.empty()) {
        photo_replay_set_status("NO REPLAY FOOTAGE BUFFERED YET", 3000);
        return;
    }

    // Sort chronologically (oldest to newest)
    std::sort(segs.begin(), segs.end(), [](const SegInfo& a, const SegInfo& b) {
        return a.mtime < b.mtime;
    });

    // Write concat manifest
    const auto list_file = dvr_dir / "concat_list.txt";
    std::ofstream out(list_file.string(), std::ios::trunc);
    for (const auto& s : segs) {
        std::string p = s.path.string();
        std::replace(p.begin(), p.end(), '\\', '/');
        out << "file '" << p << "'\n";
    }
    out.close();

    const std::string stamp = photo_replay_timestamp_str(false);
    const auto out_clip = rep_dir / ("mw3_clip_" + stamp + ".mp4");

    // Spawn async concat thread so game loop never hiccups
    std::thread([list_file, out_clip, stamp]() {
        char concat_cmd[2048]{};
        std::snprintf(concat_cmd, sizeof(concat_cmd),
                      "ffmpeg -y -f concat -safe 0 -i \"%s\" -c copy -movflags +faststart \"%s\" >nul 2>&1",
                      list_file.string().c_str(), out_clip.string().c_str());
        ::system(concat_cmd);
    }).detach();

    photo_replay_set_status("SAVED 60S REPLAY CLIP: mw3_clip_" + stamp + ".mp4", 5000);
}

void photo_replay_save_replay_file() {
    if (photo_replay.replay_buf.empty()) {
        photo_replay_set_status("REPLAY BUFFER EMPTY", 2500);
        return;
    }
    std::error_code ec;
    const auto rep_dir = photo_replay_root_dir() / "replays";
    std::filesystem::create_directories(rep_dir, ec);
    const std::string fname = "mw3_" + photo_replay_timestamp_str(false) + ".mw3replay";
    const auto path = rep_dir / fname;
    const auto latest = rep_dir / "latest.mw3replay";
    if (photo_replay.replay_buf.save_to_file(path.string())) {
        std::filesystem::copy_file(path, latest, std::filesystem::copy_options::overwrite_existing, ec);
        photo_replay_set_status("SAVED REPLAY: " + fname, 4500);
    } else {
        photo_replay_set_status("REPLAY SAVE FAILED", 3500);
    }
}

void photo_replay_load_replay_file(const std::string& custom_path = {}) {
    std::error_code ec;
    const auto rep_dir = photo_replay_root_dir() / "replays";
    std::filesystem::path target_path = custom_path.empty() ? (rep_dir / "latest.mw3replay") : std::filesystem::path(custom_path);
    if (!std::filesystem::exists(target_path, ec)) {
        // Pick newest .mw3replay in local/replays
        std::filesystem::file_time_type newest_time{};
        for (const auto& entry : std::filesystem::directory_iterator(rep_dir, ec)) {
            if (entry.path().extension() == ".mw3replay") {
                const auto wt = entry.last_write_time(ec);
                if (target_path.empty() || !std::filesystem::exists(target_path, ec) || wt > newest_time) {
                    newest_time = wt;
                    target_path = entry.path();
                }
            }
        }
    }
    if (!std::filesystem::exists(target_path, ec)) {
        photo_replay_set_status("NO .MW3REPLAY FILE FOUND", 3500);
        return;
    }
    if (photo_replay.replay_buf.load_from_file(target_path.string())) {
        photo_replay.mode = mw34::photo_replay::Mode::Replay;
        photo_replay.paused = true;
        photo_replay.replay_cur_frame = 0;
        photo_replay.replay_playhead_sec = 0.0f;
        photo_replay.replay_subframe_alpha = 0.0f;
        photo_replay_restore_snapshot(0, 0.0f);
        photo_replay_set_status("LOADED REPLAY: " + target_path.filename().string(), 4500);
    } else {
        photo_replay_set_status("FAILED TO LOAD REPLAY FILE", 3500);
    }
}



void photo_replay_exit_to_live(bool from_escape) {
    if (photo_replay.mode != mw34::photo_replay::Mode::Live && !photo_replay.replay_buf.empty()) {
        photo_replay_restore_snapshot(photo_replay.replay_buf.frame_count() - 1, 0.0f);
    }
    photo_replay_restore_player_cam_state();
    photo_replay.mode = mw34::photo_replay::Mode::Live;
    photo_replay.paused = false;
    photo_replay.camera_mode = mw34::photo_replay::CameraMode::Game;
    photo_replay.hide_hud = false;
    photo_replay.show_legend = false;
    photo_replay.status_banner.clear();
    if (from_escape) {
        photo_replay.suppress_escape_until = std::chrono::steady_clock::now() + std::chrono::milliseconds(450);
    }
    photo_replay_flush_di_keyboard();
}

void photo_replay_poll_controls() {
    mw34::vkscene::HostFpEnvironment fp;
    using namespace mw34::photo_replay;

    if (!photo_replay.cli_checked) {
        photo_replay.cli_checked = true;
        if (const char* load_env = std::getenv("MW34_LOAD_REPLAY"); load_env && *load_env) {
            photo_replay_load_replay_file(load_env);
        }
    }

    const auto now = std::chrono::steady_clock::now();
    float real_dt = 1.0f / 60.0f;
    if (photo_replay.poll_time_init) {
        real_dt = std::clamp(std::chrono::duration<float>(now - photo_replay.last_poll_time).count(), 0.001f, 0.1f);
    }
    photo_replay.last_poll_time = now;
    photo_replay.poll_time_init = true;
    if (photo_replay.video_recording) {
        real_dt = 1.0f / 60.0f; // Fixed 60.0 FPS timestep during video export
    }

    if (!photo_replay.status_banner.empty() && now > photo_replay.status_until) {
        photo_replay.status_banner.clear();
    }

    // Only poll keyboard/mouse when the game window is active (or in headless/env test mode)
    const HWND fg = ::GetForegroundWindow();
    const bool window_active = (!host.display.window) || (fg == host.display.window) || ::IsChild(host.display.window, fg);
    std::array<bool, 256> cur_keys{};
    if (window_active) {
        for (int vk = 1; vk < 255; ++vk) {
            cur_keys[vk] = (::GetAsyncKeyState(vk) & 0x8000) != 0;
        }
    }
    auto key_down = [&](int vk) { return cur_keys[vk]; };
    auto key_pressed = [&](int vk) { return cur_keys[vk] && !photo_replay.prev_keys[vk]; };
    const bool shift_held = key_down(VK_SHIFT) || key_down(VK_LSHIFT) || key_down(VK_RSHIFT);

    // Check DVR env setting once
    if (!photo_replay.dvr_checked) {
        photo_replay.dvr_checked = true;
        const char* e = std::getenv("MW34_INSTANT_REPLAY");
        photo_replay.dvr_enabled = (!e || std::strcmp(e, "0") != 0);
    }

    const unsigned vw = host.presenter && host.presenter->remaster_width() ? host.presenter->remaster_width() : (host.display.width ? host.display.width : 640);
    const unsigned vh = host.presenter && host.presenter->remaster_height() ? host.presenter->remaster_height() : (host.display.height ? host.display.height : 480);

    // Auto-manage DVR background buffer in 3D mission
    if (photo_replay.dvr_enabled && !frontend_on() && !photo_replay.dvr_pipeline.active && vw > 0 && vh > 0) {
        photo_replay_start_dvr(vw, vh);
    } else if (frontend_on() && photo_replay.dvr_pipeline.active) {
        photo_replay_stop_dvr();
    }

    // F1: Toggle On-Screen Hotkey Legend
    if (key_pressed(VK_F1)) {
        photo_replay.show_legend = !photo_replay.show_legend;
    }

    // ESC: Exit Photo/Replay/FreeCam mode entirely, remove legend from screen, and auto-restore HUD & player camera
    if (key_pressed(VK_ESCAPE) && !frontend_on()) {
        if (photo_replay.mode != Mode::Live || photo_replay.camera_mode != CameraMode::Game ||
            photo_replay.hide_hud || photo_replay.show_legend) {
            photo_replay_exit_to_live(true);
            photo_replay.prev_keys = cur_keys;
            return;
        }
    }

    // F9 / Shift+F9: Screenshot or 60 FPS Video Capture
    if (key_pressed(VK_F9)) {
        if (shift_held) {
            photo_replay_start_video(vw, vh);
        } else {
            photo_replay.screenshot_requested = true;
        }
    }

    // F10: Save 60s Instant Replay Clip
    if (key_pressed(VK_F10) && !frontend_on()) {
        photo_replay_save_instant_replay_clip();
    }

    // F11: Photo Mode / Free Cam; Shift+F11: In-Engine Rewind Replay
    if (key_pressed(VK_F11) && !frontend_on()) {
        if (shift_held) {
            if (photo_replay.mode != Mode::Replay) {
                if (photo_replay.mode == Mode::Live) {
                    photo_replay_save_player_cam_state();
                    photo_replay_record_live_snapshot();
                }
                photo_replay.mode = Mode::Replay;
                photo_replay.paused = true;
                photo_replay.show_legend = true;
                if (!photo_replay.replay_buf.empty()) {
                    photo_replay.replay_cur_frame = photo_replay.replay_buf.frame_count() - 1;
                    photo_replay.replay_playhead_sec = photo_replay.replay_buf.total_duration_sec();
                    photo_replay.replay_subframe_alpha = 0.0f;
                }
                photo_replay_set_status("IN-ENGINE REPLAY (SPACE:PLAY/PAUSE, L/R:SCRUB, C:CAM)");
            } else {
                photo_replay_exit_to_live(false);
            }
        } else {
            if (photo_replay.mode != Mode::Photo) {
                if (photo_replay.mode == Mode::Live) {
                    photo_replay_save_player_cam_state();
                    photo_replay_record_live_snapshot();
                }
                photo_replay.mode = Mode::Photo;
                photo_replay.paused = true;
                photo_replay.show_legend = true;
                if (photo_replay.camera_mode == CameraMode::Game) {
                    photo_replay_init_detached_camera(CameraMode::FreeFly);
                }
                photo_replay_set_status("PHOTO MODE ACTIVE (FREE CAM)");
            } else {
                photo_replay_exit_to_live(false);
            }
        }
    }

    const bool active_tool = (photo_replay.mode != Mode::Live) || (photo_replay.camera_mode != CameraMode::Game);
    if (active_tool) {
        // Drain DirectInput keyboard events while in Photo/Replay mode so hotkeys like 'C' never queue up and toggle the player's camera on exit
        photo_replay_flush_di_keyboard();

        // C: Cycle Camera Mode (FreeFly -> Orbit -> Dolly -> Game)
        if (key_pressed('C')) {
            CameraMode next_cm = CameraMode::FreeFly;
            if (photo_replay.camera_mode == CameraMode::FreeFly) next_cm = CameraMode::Orbit;
            else if (photo_replay.camera_mode == CameraMode::Orbit) next_cm = CameraMode::Dolly;
            else if (photo_replay.camera_mode == CameraMode::Dolly) next_cm = CameraMode::Game;
            else next_cm = CameraMode::FreeFly;
            photo_replay_init_detached_camera(next_cm);
            photo_replay_set_status(std::string("CAMERA: ") + camera_mode_name(next_cm));
        }

        // H: Toggle HUD & Cockpit interior suppression
        if (key_pressed('H')) {
            photo_replay.hide_hud = !photo_replay.hide_hud;
            photo_replay_set_status(photo_replay.hide_hud ? "HUD & COCKPIT HIDDEN" : "HUD SHOWN");
        }

        // R: Reset camera roll and FOV
        if (key_pressed('R')) {
            photo_replay.free_cam.reset_roll_and_fov(60.0f);
            photo_replay.orbit_cam.roll_rad = 0.0f;
            photo_replay.orbit_cam.fov_deg = 60.0f;
            photo_replay.orbit_cam.pan_offset = {0.f, 0.f, 0.f};
            photo_replay_set_status("RESET ROLL & FOV (60 DEG)");
        }

        // Orbit Target cycling (Tab, [, ])
        if (photo_replay.camera_mode == CameraMode::Orbit) {
            if (photo_replay.current_orbit_targets.empty()) {
                photo_replay_collect_orbit_targets(photo_replay.current_orbit_targets);
            }
            if (!photo_replay.current_orbit_targets.empty()) {
                if (key_pressed(VK_TAB) || key_pressed(VK_OEM_6)) {
                    photo_replay.orbit_target_idx = (photo_replay.orbit_target_idx + 1) % photo_replay.current_orbit_targets.size();
                    photo_replay.orbit_cam.pan_offset = {0.f, 0.f, 0.f};
                } else if (key_pressed(VK_OEM_4)) {
                    photo_replay.orbit_target_idx = (photo_replay.orbit_target_idx + photo_replay.current_orbit_targets.size() - 1) % photo_replay.current_orbit_targets.size();
                    photo_replay.orbit_cam.pan_offset = {0.f, 0.f, 0.f};
                }
            }
        }

        // Dolly Spline Keyframe controls (K: add, Backspace: delete last, P: play/pause spline)
        if (photo_replay.camera_mode == CameraMode::Dolly) {
            if (key_pressed('K')) {
                photo_replay.dolly_cam.add_keyframe(photo_replay.free_cam.to_matrix(), photo_replay.free_cam.fov_deg, 2.5f);
                photo_replay_set_status("ADDED DOLLY KEYFRAME #" + std::to_string(photo_replay.dolly_cam.keyframes.size()));
            }
            if (key_pressed(VK_BACK)) {
                photo_replay.dolly_cam.remove_last();
                photo_replay_set_status("REMOVED LAST DOLLY KEYFRAME");
            }
            if (key_pressed('P')) {
                if (photo_replay.dolly_cam.keyframes.size() >= 2) {
                    photo_replay.dolly_cam.playing = !photo_replay.dolly_cam.playing;
                    if (photo_replay.dolly_cam.playing && photo_replay.dolly_cam.playhead_sec >= photo_replay.dolly_cam.duration_sec) {
                        photo_replay.dolly_cam.playhead_sec = 0.0f;
                    }
                } else {
                    photo_replay_set_status("ADD AT LEAST 2 KEYFRAMES WITH [K] FIRST");
                }
            }
            if (photo_replay.dolly_cam.playing) {
                photo_replay.dolly_cam.playhead_sec += real_dt * photo_replay.playback_speed;
                if (photo_replay.dolly_cam.playhead_sec > photo_replay.dolly_cam.duration_sec) {
                    if (photo_replay.dolly_cam.loop) {
                        photo_replay.dolly_cam.playhead_sec = 0.0f;
                    } else {
                        photo_replay.dolly_cam.playhead_sec = photo_replay.dolly_cam.duration_sec;
                        photo_replay.dolly_cam.playing = false;
                    }
                }
            }
        }

        // Replay timeline controls
        if (photo_replay.mode == Mode::Replay && !photo_replay.replay_buf.empty()) {
            const float total_dur = photo_replay.replay_buf.total_duration_sec();
            if (key_pressed(VK_SPACE)) {
                photo_replay.paused = !photo_replay.paused;
                if (!photo_replay.paused && photo_replay.replay_cur_frame + 1 >= photo_replay.replay_buf.frame_count()) {
                    photo_replay.replay_cur_frame = 0;
                    photo_replay.replay_playhead_sec = 0.0f;
                    photo_replay.replay_subframe_alpha = 0.0f;
                }
            }
            // Speed presets: 1=0.1x, 2=0.25x, 3=0.5x, 4=1.0x, 5=2.0x, 6=4.0x
            if (key_pressed('1')) photo_replay.playback_speed = 0.1f;
            if (key_pressed('2')) photo_replay.playback_speed = 0.25f;
            if (key_pressed('3')) photo_replay.playback_speed = 0.5f;
            if (key_pressed('4')) photo_replay.playback_speed = 1.0f;
            if (key_pressed('5')) photo_replay.playback_speed = 2.0f;
            if (key_pressed('6')) photo_replay.playback_speed = 4.0f;

            // Single-frame step (< / , and > / .)
            if (key_pressed(VK_OEM_COMMA)) {
                photo_replay.paused = true;
                if (photo_replay.replay_cur_frame > 0) --photo_replay.replay_cur_frame;
                photo_replay.replay_subframe_alpha = 0.0f;
                const float t0 = photo_replay.replay_buf.frame(0).mission_time_sec;
                photo_replay.replay_playhead_sec = std::max(0.0f, photo_replay.replay_buf.frame(photo_replay.replay_cur_frame).mission_time_sec - t0);
            }
            if (key_pressed(VK_OEM_PERIOD)) {
                photo_replay.paused = true;
                if (photo_replay.replay_cur_frame + 1 < photo_replay.replay_buf.frame_count()) ++photo_replay.replay_cur_frame;
                photo_replay.replay_subframe_alpha = 0.0f;
                const float t0 = photo_replay.replay_buf.frame(0).mission_time_sec;
                photo_replay.replay_playhead_sec = std::max(0.0f, photo_replay.replay_buf.frame(photo_replay.replay_cur_frame).mission_time_sec - t0);
            }

            // Rewind / Fast-Scrub (Left / Right arrows when not holding Right Mouse Button)
            const bool rmb_look = key_down(VK_RBUTTON);
            if (!rmb_look && (key_pressed(VK_LEFT) || key_pressed(VK_RIGHT))) {
                const float jump = (shift_held ? 5.0f : 1.0f) * (key_pressed(VK_LEFT) ? -1.0f : 1.0f);
                photo_replay.replay_playhead_sec = std::clamp(photo_replay.replay_playhead_sec + jump, 0.0f, total_dur);
                photo_replay.replay_cur_frame = photo_replay.replay_buf.find_frame_by_time(photo_replay.replay_playhead_sec);
                photo_replay.replay_subframe_alpha = 0.0f;
            }
            if (key_pressed(VK_HOME)) {
                photo_replay.replay_playhead_sec = 0.0f;
                photo_replay.replay_cur_frame = 0;
                photo_replay.replay_subframe_alpha = 0.0f;
            }
            if (key_pressed(VK_END)) {
                photo_replay.replay_playhead_sec = total_dur;
                photo_replay.replay_cur_frame = photo_replay.replay_buf.frame_count() - 1;
                photo_replay.replay_subframe_alpha = 0.0f;
            }
            if (shift_held && key_pressed(VK_F8)) {
                photo_replay_save_replay_file();
            } else if (key_pressed(VK_F8)) {
                photo_replay_load_replay_file();
            }

            // Advance replay playhead when playing
            if (!photo_replay.paused) {
                photo_replay.replay_playhead_sec += real_dt * photo_replay.playback_speed;
                if (photo_replay.replay_playhead_sec >= total_dur) {
                    photo_replay.replay_playhead_sec = total_dur;
                    photo_replay.replay_cur_frame = photo_replay.replay_buf.frame_count() - 1;
                    photo_replay.replay_subframe_alpha = 0.0f;
                    photo_replay.paused = true;
                } else {
                    const std::size_t idx = photo_replay.replay_buf.find_frame_by_time(photo_replay.replay_playhead_sec);
                    photo_replay.replay_cur_frame = idx;
                    const float t_base = photo_replay.replay_buf.frame(0).mission_time_sec;
                    const float t_cur = photo_replay.replay_buf.frame(idx).mission_time_sec - t_base;
                    if (idx + 1 < photo_replay.replay_buf.frame_count()) {
                        const float t_next = photo_replay.replay_buf.frame(idx + 1).mission_time_sec - t_base;
                        const float span = std::max(1e-4f, t_next - t_cur);
                        photo_replay.replay_subframe_alpha = std::clamp((photo_replay.replay_playhead_sec - t_cur) / span, 0.0f, 1.0f);
                    } else {
                        photo_replay.replay_subframe_alpha = 0.0f;
                    }
                }
            }
        }

        // Camera 6-DOF movement & DirectInput + Win32 mouse look
        float mouse_dx = photo_replay.accum_di_dx;
        float mouse_dy = photo_replay.accum_di_dy;
        float mouse_dz = photo_replay.accum_di_dz;
        photo_replay.accum_di_dx = 0.0f;
        photo_replay.accum_di_dy = 0.0f;
        photo_replay.accum_di_dz = 0.0f;

        if (window_active) {
            for (const auto& [g_dev, fmt_sz] : host.di_format) {
                if (fmt_sz == 16) {
                    if (auto* co = host.com_object(g_dev); co && co->native) {
                        auto* dv = reinterpret_cast<IDirectInputDeviceA*>(co->native);
                        IDirectInputDevice2A* d2 = nullptr;
                        if (SUCCEEDED(dv->QueryInterface(IID_IDirectInputDevice2A, reinterpret_cast<void**>(&d2))) && d2) {
                            d2->Poll();
                            d2->Release();
                        }
                        DIMOUSESTATE ms{};
                        HRESULT hr = dv->GetDeviceState(sizeof(ms), &ms);
                        if (FAILED(hr)) {
                            dv->Acquire();
                            hr = dv->GetDeviceState(sizeof(ms), &ms);
                        }
                        if (SUCCEEDED(hr)) {
                            mouse_dx += float(ms.lX);
                            mouse_dy += float(ms.lY);
                            mouse_dz += float(ms.lZ);
                        }
                    }
                }
            }
        }

        POINT pt{};
        if (window_active && ::GetCursorPos(&pt)) {
            if (photo_replay.mouse_init) {
                mouse_dx += float(pt.x - photo_replay.last_mouse_pt.x);
                mouse_dy += float(pt.y - photo_replay.last_mouse_pt.y);
            }
            photo_replay.last_mouse_pt = pt;
            photo_replay.mouse_init = true;
        }

        // Allow Arrow keys (in Photo Mode or when holding RMB in Replay) and IJKL to rotate/orbit the camera
        const bool arrows_rotate = (photo_replay.mode != Mode::Replay) || key_down(VK_RBUTTON);
        if (arrows_rotate) {
            if (key_down(VK_LEFT))  mouse_dx -= 240.0f * real_dt;
            if (key_down(VK_RIGHT)) mouse_dx += 240.0f * real_dt;
            if (key_down(VK_UP))    mouse_dy -= 190.0f * real_dt;
            if (key_down(VK_DOWN))  mouse_dy += 190.0f * real_dt;
        } else {
            if (key_down(VK_UP))    mouse_dy -= 190.0f * real_dt;
            if (key_down(VK_DOWN))  mouse_dy += 190.0f * real_dt;
        }
        if (key_down('J')) mouse_dx -= 240.0f * real_dt;
        if (key_down('L')) mouse_dx += 240.0f * real_dt;
        if (key_down('I')) mouse_dy -= 190.0f * real_dt;
        if (photo_replay.camera_mode != CameraMode::Dolly && key_down('K')) mouse_dy += 190.0f * real_dt;

        const float move_fwd   = (key_down('W') ? 1.0f : 0.0f) - (key_down('S') ? 1.0f : 0.0f);
        const float move_right = (key_down('D') ? 1.0f : 0.0f) - (key_down('A') ? 1.0f : 0.0f);
        const float move_up    = (key_down('E') ? 1.0f : 0.0f) - (key_down('Q') ? 1.0f : 0.0f);
        const float roll_dir   = (key_down('X') ? 1.0f : 0.0f) - (key_down('Z') ? 1.0f : 0.0f);
        const float fov_delta  = ((key_down(VK_NEXT) ? 1.0f : 0.0f) - (key_down(VK_PRIOR) ? 1.0f : 0.0f)) * 35.0f * real_dt;
        const float spd_mult   = shift_held ? 3.0f : (key_down(VK_CONTROL) ? 0.25f : 1.0f);

        if (key_pressed(VK_OEM_PLUS)) {
            photo_replay.free_cam.move_speed = std::clamp(photo_replay.free_cam.move_speed * 1.25f, 2.0f, 500.0f);
        }
        if (key_pressed(VK_OEM_MINUS)) {
            photo_replay.free_cam.move_speed = std::clamp(photo_replay.free_cam.move_speed * 0.8f, 2.0f, 500.0f);
        }

        if (photo_replay.camera_mode == CameraMode::FreeFly ||
            (photo_replay.camera_mode == CameraMode::Dolly && !photo_replay.dolly_cam.playing)) {
            const float wheel_fov = -(mouse_dz / 120.0f) * 2.5f;
            photo_replay.free_cam.fov_deg = std::clamp(photo_replay.free_cam.fov_deg + fov_delta + wheel_fov, 10.0f, 120.0f);
            photo_replay.free_cam.step(real_dt, move_fwd, move_right, move_up,
                                       mouse_dx, mouse_dy, roll_dir, spd_mult);
        } else if (photo_replay.camera_mode == CameraMode::Orbit) {
            photo_replay.orbit_cam.fov_deg = std::clamp(photo_replay.orbit_cam.fov_deg + fov_delta, 10.0f, 120.0f);
            // In Orbit mode: mouse X/Y AND A/D + Q/E orbit around the target, W/S + mouse wheel zoom distance
            const float orbit_dx = mouse_dx + move_right * 260.0f * spd_mult * real_dt;
            const float orbit_dy = mouse_dy + move_up * 200.0f * spd_mult * real_dt;
            const float dolly_in = move_fwd * spd_mult + (mouse_dz / 120.0f) * 4.0f;
            photo_replay.orbit_cam.step(real_dt, orbit_dx, orbit_dy, dolly_in, 0.0f, 0.0f, roll_dir);
        }
    } else {
        photo_replay.mouse_init = false;
        photo_replay.accum_di_dx = 0.0f;
        photo_replay.accum_di_dy = 0.0f;
        photo_replay.accum_di_dz = 0.0f;
    }

    photo_replay.prev_keys = cur_keys;
}


// Draws the On-Screen Hotkey Legend & Replay Scrubber onto the Vulkan resident target AFTER clean capture
void photo_replay_overlay_gpu(unsigned w, unsigned h) {
    using namespace mw34::photo_replay;
    OverlayRenderState st{};
    st.mode = photo_replay.mode;
    st.camera_mode = photo_replay.camera_mode;
    st.show_legend = photo_replay.show_legend;
    st.paused = (photo_replay.mode == Mode::Photo) ? true : photo_replay.paused;
    st.hide_hud = photo_replay.hide_hud;
    st.video_recording = photo_replay.video_recording;
    st.video_frames_captured = photo_replay.video_pipeline.frames_written;
    st.fov_deg = (photo_replay.camera_mode == CameraMode::Orbit) ? photo_replay.orbit_cam.fov_deg : photo_replay.free_cam.fov_deg;
    st.fly_speed = photo_replay.free_cam.move_speed;
    st.playback_speed = photo_replay.playback_speed;
    st.replay_cur_sec = photo_replay.replay_playhead_sec;
    st.replay_total_sec = photo_replay.replay_buf.total_duration_sec();
    st.replay_cur_frame = photo_replay.replay_cur_frame;
    st.replay_total_frames = photo_replay.replay_buf.frame_count();
    st.dolly_keyframes = photo_replay.dolly_cam.keyframes.size();
    st.dolly_playing = photo_replay.dolly_cam.playing;
    if (!photo_replay.current_orbit_targets.empty()) {
        st.orbit_target_label = photo_replay.current_orbit_targets[photo_replay.orbit_target_idx % photo_replay.current_orbit_targets.size()].label;
    }
    st.status_banner = photo_replay.status_banner;

    std::vector<std::uint32_t> canvas;
    if (!render_overlay_canvas(st, w, h, canvas)) return;

    namespace vs = mw34::vkscene;
    hud_sc = vs::Scene{};
    hud_sc.hud = true;
    hud_sc.width = w;
    hud_sc.height = h;
    hud_sc.has_depth = host.res_zb != 0;
    hud_w = w;
    hud_h = h;

    vs::TextureRef r{};
    r.key = 0x50484f544f4f564cULL;
    r.width = w;
    r.height = h;
    r.format = vs::TexFormat::rgba8888;
    r.pixels32 = std::move(canvas);
    std::uint64_t hash = 0xcbf29ce484222325ULL;
    for (std::size_t i = 0; i < r.pixels32.size(); i += 7) {
        hash ^= r.pixels32[i];
        hash *= 0x100000001b3ULL;
    }
    hash ^= std::uint64_t(host.frames);
    r.hash = hash;
    hud_sc.textures.push_back(std::move(r));

    const unsigned first = 0;
    hud_vertex(-0.5f, -0.5f, 0xffffffffu, 0, 0);
    hud_vertex(float(w) - 0.5f, -0.5f, 0xffffffffu, 1, 0);
    hud_vertex(float(w) - 0.5f, float(h) - 0.5f, 0xffffffffu, 1, 1);
    hud_vertex(-0.5f, -0.5f, 0xffffffffu, 0, 0);
    hud_vertex(float(w) - 0.5f, float(h) - 0.5f, 0xffffffffu, 1, 1);
    hud_vertex(-0.5f, float(h) - 0.5f, 0xffffffffu, 0, 1);
    hud_draw(0, false, first, WideWorld);
    hud_sc.color.resize(std::size_t(w) * h);
    hud_sc.depth.resize(hud_sc.color.size());
    try {
        struct PhotoInternalScope {
            Stage& s;
            bool was;
            explicit PhotoInternalScope(Stage& x) : s(x), was(x.host_internal) { s.host_internal = true; }
            ~PhotoInternalScope() { s.host_internal = was; }
        } hi(*this);
        host.sren->render(hud_sc, false, false);
    } catch (const std::exception& e) {
        deny(std::string(e.what()), 0);
    }
    hud_sc = vs::Scene{};
}

void photo_replay_on_present(unsigned w, unsigned h, bool is_direct, const std::vector<unsigned char>& fallback_px, unsigned pitch) {
    const bool record_on = photo_replay.video_recording && photo_replay.video_pipeline.active;
    const bool dvr_on = photo_replay.dvr_enabled && !frontend_on() && photo_replay.dvr_pipeline.active;

    if (photo_replay.screenshot_requested || record_on || dvr_on) {
        if (is_direct && host.presenter) {
            static auto last_rec_capture = std::chrono::steady_clock::time_point{};
            const auto now = std::chrono::steady_clock::now();
            const bool time_for_video = (record_on || dvr_on) &&
                (std::chrono::duration<float>(now - last_rec_capture).count() >= (1.0f / 62.0f));

            if (photo_replay.screenshot_requested || time_for_video) {
                std::vector<std::uint8_t> raw_rgba;
                unsigned cap_w = 0, cap_h = 0;
                host.presenter->capture_fullres_bgra(raw_rgba, cap_w, cap_h);

                if (photo_replay.screenshot_requested) {
                    photo_replay.screenshot_requested = false;
                    std::error_code ec;
                    const auto shot_dir = photo_replay_root_dir() / "screenshots";
                    std::filesystem::create_directories(shot_dir, ec);
                    const std::string fname = "mw3_" + photo_replay_timestamp_str(true) + ".png";
                    const auto full_path = shot_dir / fname;
                    if (mw34::photo_replay::encode_and_save_png_bgra(full_path.string(), raw_rgba.data(), cap_w, cap_h)) {
                        photo_replay_set_status("SCREENSHOT SAVED: " + fname, 4000);
                    } else {
                        photo_replay_set_status("SCREENSHOT SAVE FAILED", 3500);
                    }
                }

                if (time_for_video && !raw_rgba.empty()) {
                    last_rec_capture = now;
                    if (record_on) {
                        photo_replay.video_pipeline.push_frame(raw_rgba.data(), cap_w, cap_h);
                    }
                    if (dvr_on) {
                        photo_replay.dvr_pipeline.push_frame(raw_rgba.data(), cap_w, cap_h);
                    }
                }
            }
        } else if (!fallback_px.empty() && photo_replay.screenshot_requested) {
            photo_replay.screenshot_requested = false;
            std::vector<std::uint8_t> rgb(std::size_t(w) * h * 3);
            for (unsigned y = 0; y < h; ++y) {
                for (unsigned x = 0; x < w; ++x) {
                    const unsigned p = unsigned(fallback_px[std::size_t(y) * pitch + 2 * x]) |
                                       (unsigned(fallback_px[std::size_t(y) * pitch + 2 * x + 1]) << 8);
                    std::uint8_t* o = &rgb[(std::size_t(y) * w + x) * 3];
                    o[0] = static_cast<std::uint8_t>(((p >> 11) & 31) * 255 / 31);
                    o[1] = static_cast<std::uint8_t>(((p >> 5) & 63) * 255 / 63);
                    o[2] = static_cast<std::uint8_t>((p & 31) * 255 / 31);
                }
            }
            std::error_code ec;
            const auto shot_dir = photo_replay_root_dir() / "screenshots";
            std::filesystem::create_directories(shot_dir, ec);
            const std::string fname = "mw3_" + photo_replay_timestamp_str(true) + ".png";
            mw34::photo_replay::write_png_file((shot_dir / fname).string(), rgb.data(), w, h);
            photo_replay_set_status("SCREENSHOT SAVED: " + fname, 4000);
        }
    }
    if (is_direct && host.presenter) {
        photo_replay_overlay_gpu(w, h);
    }
}

void* photo_replay_skip_call(State* s, void* p, unsigned stack_arg_bytes, unsigned ret_eax = 0) {
    const unsigned sp = state.gpr.rsp.dword;
    const unsigned ret_addr = load(sp);
    state.gpr.rax.dword = ret_eax;
    state.gpr.rip.dword = ret_addr;
    state.gpr.rsp.dword = sp + 4 + stack_arg_bytes;
    return returned(s, ret_addr, p);
}

template <class Next>
void* photo_replay_body(State* s, unsigned target, void* p, Next&& next) {
    // Player-camera target markers are not valid for a detached camera. Frozen
    // frames also skip their projection update, even when Photo uses Game view.
    // Suppress only this display routine; retain the live camera-provenance guard.
    // Original 0x441490 is a thiscall with one stack argument (ret 4).
    if (target == 0x441490 && (photo_replay_sim_frozen() || photo_replay_detached_cam())) {
        return photo_replay_skip_call(s, p, 4, 0);
    }

    // Track active scene node transform blocks for smooth slow-motion interpolation & orbit target discovery
    if ((target == 0x4fc300 || target == 0x4ed280) && photo_replay.tracked_node_datas.size() < 4096) {
        const unsigned node = state.gpr.rcx.dword;
        if (node && readable(node, 0x3c)) {
            const unsigned data = load(node + 0x38);
            if (data && readable(data, 0x60)) {
                photo_replay.tracked_node_datas.insert(data);
            }
        }
    }

    // Mission frame driver (0x481E70): poll hotkeys/camera and restore replay state when frozen/replaying
    if (target == 0x481e70) {
        photo_replay_poll_controls();
        if (photo_replay_sim_frozen()) {
            photo_replay_restore_snapshot(photo_replay.replay_cur_frame, photo_replay.replay_subframe_alpha);
        }
        return next();
    }

    // Frame timer update (0x575A00): zero dt when simulation is frozen in Photo/Replay mode
    if (target == 0x575a00 && photo_replay_sim_frozen()) {
        void* r = next();
        if (writable(0x72c52c, 12)) {
            store(0x72c52c, 0);
            store(0x72c534, 0);
        }
        return r;
    }

    // Simulation step routines inside 0x481E70: skip when frozen in Photo/Replay mode
    if (photo_replay_sim_frozen()) {
        if (target == 0x4a8cd0 || target == 0x48f470 || target == 0x4783a0) {
            return photo_replay_skip_call(s, p, 0, 1);
        }
        if (target == 0x40f8d0) {
            return photo_replay_skip_call(s, p, 4, 0);
        }
        if (target == 0x5a6790 || target == 0x481260) {
            return photo_replay_skip_call(s, p, 0, 0);
        }
        if (target == 0x5a67c0) {
            return photo_replay_skip_call(s, p, 8, 0);
        }
    }

    // World scene traversal entry (0x4F6DC0): record live frame snapshot right before 3D world rendering
    if (target == 0x4f6dc0) {
        const unsigned cam_node = state.gpr.rcx.dword;
        const unsigned cam_data = (cam_node && readable(cam_node + 0x38, 4)) ? load(cam_node + 0x38) : 0;
        if (distance_world(cam_node, cam_data) && photo_replay.mode == mw34::photo_replay::Mode::Live) {
            photo_replay_record_live_snapshot();
        }
    }

    // Force external view (is_cockpit_view = 0) in 0x481290, 0x481790, 0x481A10 when camera is detached
    if ((target == 0x481290 || target == 0x481790 || target == 0x481a10) && photo_replay_detached_cam()) {
        const unsigned sp = state.gpr.rsp.dword;
        if (writable(sp + 8, 4)) {
            store(sp + 8, 0);
        }
    }

    // Keep player external 3D Mech visible in 0x4EB170 when camera is detached
    if (target == 0x4eb170 && photo_replay_detached_cam()) {
        if (state.gpr.rdx.dword == 0) {
            const unsigned player_root = photo_replay_player_root_node();
            if (player_root && state.gpr.rcx.dword == player_root) {
                state.gpr.rdx.dword = 1;
            }
        }
    }

    // Suppress 3D cockpit shell overlay (0x4F7350 / 0x4F73F0) when camera is detached or HUD is hidden
    if (photo_replay_detached_cam() || photo_replay.hide_hud) {
        if (target == 0x4f7350) return photo_replay_skip_call(s, p, 0, 0);
        if (target == 0x4f73f0) return photo_replay_skip_call(s, p, 4, 0);
    }

    // Identify the shared translucent flush. Draw-level HUD roles keep world
    // water/effects visible while suppressing its HUD panels.
    if (target == 0x57e110 && photo_replay.hide_hud) {
        ++photo_replay.suppress_d3d_depth;
        try {
            void* r = next();
            --photo_replay.suppress_d3d_depth;
            return r;
        } catch (...) {
            --photo_replay.suppress_d3d_depth;
            throw;
        }
    }

    // World Camera pose & FOV injection at 0x4ED280 (called from 0x4F4370 at return address 0x4F4391)
    if (target == 0x4ed280 && readable(state.gpr.rsp.dword, 4) && load(state.gpr.rsp.dword) == 0x4f4391) {
        const unsigned node = state.gpr.rcx.dword;
        const unsigned ebp = state.gpr.rbp.dword;
        const unsigned cam_data = (node && readable(node + 0x38, 4)) ? load(node + 0x38) : (readable(ebp - 8, 4) ? load(ebp - 8) : 0);
        const bool is_world_cam = node && cam_data && readable(cam_data, 0x1e4) && distance_world(node, cam_data);
        if (is_world_cam && photo_replay_detached_cam() && writable(ebp + 8, 4)) {
            store(ebp + 8, 0); // Zero 32-bit head-bob pointer argument so 0x4F4398 skips cockpit head-bob
        }
        void* r = next();
        if (is_world_cam) {
            mw34::vkscene::HostFpEnvironment fp;
            // 0x4ED280 writes the camera world Mat3x4 to the top of the global matrix stack at 0x5EDA90,
            // which 0x4F4391 immediately reads via esi = load(load(0x5eda90)) to build the view matrix.
            const unsigned stack_ptr = readable(0x5eda90, 4) ? load(0x5eda90) : 0;
            const unsigned stack_mat = (stack_ptr && readable(stack_ptr, 4)) ? load(stack_ptr) : 0;
            const unsigned mat_addr = (stack_mat && readable(stack_mat, 48)) ? stack_mat : (cam_data + 0x60);

            if (photo_replay.camera_mode == mw34::photo_replay::CameraMode::Game) {
                photo_replay.last_world_cam_mat = photo_replay_read_mat3x4(mat_addr);
                const float v_rad = wide_float(cam_data + 0xec);
                if (v_rad > 0.05f && v_rad < 3.0f) {
                    photo_replay.last_world_cam_vfov_deg = v_rad * mw34::photo_replay::kRadToDeg;
                }
                photo_replay.has_world_cam = true;
            } else {
                float custom_fov_deg = 60.0f;
                const auto custom_mat = photo_replay_active_camera_mat(custom_fov_deg);
                if (stack_mat && writable(stack_mat, 48)) {
                    photo_replay_write_mat3x4(stack_mat, custom_mat);
                }
                // Only replace the matrix-stack result. Original 0x4F4370
                // derives the camera eye (+0x2C), world matrix (+0x44), forward
                // vector (+0x74) and renderer inverse from this exact result.
                // +0x30/+0x60 are transform-node offsets, not camera matrices.
                if (photo_replay_detached_cam() && writable(cam_data + 0x1e0, 4)) {
                    store(cam_data + 0x1e0, 0); // Force 0x4F6DC0 to re-find spatial sector for new camera position
                }
                const double v_rad = std::clamp(double(custom_fov_deg), 10.0, 120.0) * double(mw34::photo_replay::kDegToRad);
                const double aspect = wide_on() ? (3440.0 / 1440.0)
                    : (host.display.height ? double(host.display.width) / double(host.display.height) : (4.0 / 3.0));
                const double h_rad = 2.0 * std::atan(std::tan(v_rad * 0.5) * aspect);
                const double h_rad_43 = 2.0 * std::atan(std::tan(v_rad * 0.5) * (4.0 / 3.0));
                wide_store_float(cam_data + 0xe8, float(h_rad));
                wide_store_float(cam_data + 0xec, float(v_rad));
                wide_store_float(cam_data + 0xf0, float(h_rad * 0.5));
                wide_store_float(cam_data + 0xf4, float(v_rad * 0.5));
                wide_store_float(cam_data + 0x1d4, float(1.0 / std::tan(h_rad * 0.5)));
                wide_store_float(cam_data + 0x1d8, float(1.0 / std::tan(v_rad * 0.5)));
                store(cam_data + 0xf8, 1);
                store(cam_data + 0x138, 1);
                if (wide_on()) {
                    auto& wc = wide_cameras[cam_data];
                    float r_h = float(h_rad_43);
                    float r_half = float(h_rad_43 * 0.5);
                    float r_cot = float(1.0 / std::tan(h_rad_43 * 0.5));
                    std::memcpy(&wc.raw_h, &r_h, 4);
                    std::memcpy(&wc.raw_half, &r_half, 4);
                    std::memcpy(&wc.raw_cot, &r_cot, 4);
                    wc.wide_h = load(cam_data + 0xe8);
                    wc.wide_half = load(cam_data + 0xf0);
                    wc.wide_cot = load(cam_data + 0x1d4);
                    wc.applied = true;
                }
            }
        }
        return r;
    }

    return next();
}
