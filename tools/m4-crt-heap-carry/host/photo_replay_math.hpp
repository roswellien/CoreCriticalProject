#pragma once
#include <set>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <deque>
#include <fstream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

namespace mw34::photo_replay {

inline constexpr double kPi = 3.14159265358979323846;
inline constexpr float kDegToRad = static_cast<float>(kPi / 180.0);
inline constexpr float kRadToDeg = static_cast<float>(180.0 / kPi);

enum class Mode : unsigned {
    Live = 0,
    Photo = 1,
    Replay = 2
};

enum class CameraMode : unsigned {
    Game = 0,
    FreeFly = 1,
    Orbit = 2,
    Dolly = 3
};

inline constexpr std::array<float, 6> kSpeedPresets = {0.1f, 0.25f, 0.5f, 1.0f, 2.0f, 4.0f};

inline const char* mode_name(Mode m) noexcept {
    switch (m) {
        case Mode::Live: return "LIVE";
        case Mode::Photo: return "PHOTO MODE";
        case Mode::Replay: return "REPLAY MODE";
    }
    return "LIVE";
}

inline const char* camera_mode_name(CameraMode cm) noexcept {
    switch (cm) {
        case CameraMode::Game: return "GAME / COCKPIT CAM";
        case CameraMode::FreeFly: return "FREE-FLY CAM";
        case CameraMode::Orbit: return "ORBIT TARGET CAM";
        case CameraMode::Dolly: return "DOLLY SPLINE CAM";
    }
    return "GAME CAM";
}

struct Vec3 {
    float x{}, y{}, z{};

    constexpr Vec3() = default;
    constexpr Vec3(float x_, float y_, float z_) : x(x_), y(y_), z(z_) {}

    constexpr Vec3 operator+(const Vec3& o) const noexcept { return {x + o.x, y + o.y, z + o.z}; }
    constexpr Vec3 operator-(const Vec3& o) const noexcept { return {x - o.x, y - o.y, z - o.z}; }
    constexpr Vec3 operator*(float s) const noexcept { return {x * s, y * s, z * s}; }
    constexpr Vec3& operator+=(const Vec3& o) noexcept { x += o.x; y += o.y; z += o.z; return *this; }
    constexpr Vec3& operator-=(const Vec3& o) noexcept { x -= o.x; y -= o.y; z -= o.z; return *this; }
};

inline constexpr float dot(const Vec3& a, const Vec3& b) noexcept {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

inline constexpr Vec3 cross(const Vec3& a, const Vec3& b) noexcept {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    };
}

inline float length_sq(const Vec3& v) noexcept { return dot(v, v); }
inline float length(const Vec3& v) noexcept { return std::sqrt(length_sq(v)); }

inline Vec3 normalize(const Vec3& v, const Vec3& fallback = {0.f, 0.f, 1.f}) noexcept {
    const float len = length(v);
    if (len < 1e-6f || !std::isfinite(len)) return fallback;
    const float inv = 1.0f / len;
    return {v.x * inv, v.y * inv, v.z * inv};
}

inline constexpr Vec3 lerp(const Vec3& a, const Vec3& b, float t) noexcept {
    return {a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t};
}

// MW3 3x4 camera/node transform matrix (12 floats = 48 bytes):
// Row 0 [0..2]: Right   (Rx, Ry, Rz)
// Row 1 [3..5]: Up      (Ux, Uy, Uz)
// Row 2 [6..8]: Back    (Bx, By, Bz) = -Forward
// Row 3 [9..11]: Pos    (Px, Py, Pz)
using Mat3x4 = std::array<float, 12>;

inline constexpr Mat3x4 identity_mat3x4() noexcept {
    return {1.f, 0.f, 0.f,
            0.f, 1.f, 0.f,
            0.f, 0.f, 1.f,
            0.f, 0.f, 0.f};
}

inline constexpr Vec3 mat_right(const Mat3x4& m) noexcept { return {m[0], m[1], m[2]}; }
inline constexpr Vec3 mat_up(const Mat3x4& m) noexcept { return {m[3], m[4], m[5]}; }
inline constexpr Vec3 mat_back(const Mat3x4& m) noexcept { return {m[6], m[7], m[8]}; }
inline constexpr Vec3 mat_forward(const Mat3x4& m) noexcept { return {-m[6], -m[7], -m[8]}; }
inline constexpr Vec3 mat_pos(const Mat3x4& m) noexcept { return {m[9], m[10], m[11]}; }

inline void set_mat_pos(Mat3x4& m, const Vec3& p) noexcept {
    m[9] = p.x;
    m[10] = p.y;
    m[11] = p.z;
}

inline bool is_valid_mat3x4(const Mat3x4& m) noexcept {
    for (float v : m) {
        if (!std::isfinite(v)) return false;
    }
    const float r2 = m[0] * m[0] + m[1] * m[1] + m[2] * m[2];
    const float u2 = m[3] * m[3] + m[4] * m[4] + m[5] * m[5];
    const float b2 = m[6] * m[6] + m[7] * m[7] + m[8] * m[8];
    return r2 > 0.25f && u2 > 0.25f && b2 > 0.25f && r2 < 4.0f && u2 < 4.0f && b2 < 4.0f;
}

// Exact inverse of MW3's 0x523BC0 Euler extractor:
//   pitch = asin(-B.y)
//   yaw   = atan2(B.x, B.z)
//   roll  = atan2(R.y, U.y)
inline Mat3x4 euler_to_mat3x4(float pitch_rad, float yaw_rad, float roll_rad, const Vec3& pos) noexcept {
    const float cp = std::cos(pitch_rad), sp = std::sin(pitch_rad);
    const float cy = std::cos(yaw_rad),   sy = std::sin(yaw_rad);
    const float cr = std::cos(roll_rad),  sr = std::sin(roll_rad);

    const Vec3 back{sy * cp, -sp, cy * cp};
    const Vec3 right0{cy, 0.f, -sy};
    const Vec3 up0{sy * sp, cp, cy * sp};

    const Vec3 right = right0 * cr + up0 * sr;
    const Vec3 up    = right0 * (-sr) + up0 * cr;

    return {
        right.x, right.y, right.z,
        up.x,    up.y,    up.z,
        back.x,  back.y,  back.z,
        pos.x,   pos.y,   pos.z
    };
}

inline void mat3x4_to_euler(const Mat3x4& m, float& pitch_rad, float& yaw_rad, float& roll_rad) noexcept {
    const float by = std::clamp(m[7], -1.0f, 1.0f);
    pitch_rad = std::asin(-by);
    if (std::abs(by) < 0.9999f) {
        yaw_rad = std::atan2(m[6], m[8]);
        roll_rad = std::atan2(m[1], m[4]);
    } else {
        yaw_rad = std::atan2(-m[2], m[0]);
        roll_rad = 0.0f;
    }
}

struct Quat {
    float x{}, y{}, z{}, w{1.f};

    Quat normalize() const noexcept {
        const float n = std::sqrt(x * x + y * y + z * z + w * w);
        if (n < 1e-6f || !std::isfinite(n)) return {0.f, 0.f, 0.f, 1.f};
        const float inv = 1.0f / n;
        return {x * inv, y * inv, z * inv, w * inv};
    }

    static Quat from_mat3x4(const Mat3x4& m) noexcept {
        const Vec3 r = mw34::photo_replay::normalize(mat_right(m), {1.f, 0.f, 0.f});
        const Vec3 b = mw34::photo_replay::normalize(mat_back(m), {0.f, 0.f, 1.f});
        const Vec3 u = mw34::photo_replay::normalize(cross(b, r), {0.f, 1.f, 0.f});
        const float m00 = r.x, m01 = r.y, m02 = r.z;
        const float m10 = u.x, m11 = u.y, m12 = u.z;
        const float m20 = b.x, m21 = b.y, m22 = b.z;
        const float tr = m00 + m11 + m22;
        Quat q{};
        if (tr > 0.0f) {
            const float s = std::sqrt(tr + 1.0f) * 2.0f;
            q.w = 0.25f * s;
            q.x = (m21 - m12) / s;
            q.y = (m02 - m20) / s;
            q.z = (m10 - m01) / s;
        } else if (m00 > m11 && m00 > m22) {
            const float s = std::sqrt(1.0f + m00 - m11 - m22) * 2.0f;
            q.w = (m21 - m12) / s;
            q.x = 0.25f * s;
            q.y = (m01 + m10) / s;
            q.z = (m02 + m20) / s;
        } else if (m11 > m22) {
            const float s = std::sqrt(1.0f + m11 - m00 - m22) * 2.0f;
            q.w = (m02 - m20) / s;
            q.x = (m01 + m10) / s;
            q.y = 0.25f * s;
            q.z = (m12 + m21) / s;
        } else {
            const float s = std::sqrt(1.0f + m22 - m00 - m11) * 2.0f;
            q.w = (m10 - m01) / s;
            q.x = (m02 + m20) / s;
            q.y = (m12 + m21) / s;
            q.z = 0.25f * s;
        }
        return q.normalize();
    }

    Mat3x4 to_mat3x4(const Vec3& pos) const noexcept {
        const Quat q = normalize();
        const float xx = q.x * q.x, yy = q.y * q.y, zz = q.z * q.z;
        const float xy = q.x * q.y, xz = q.x * q.z, yz = q.y * q.z;
        const float wx = q.w * q.x, wy = q.w * q.y, wz = q.w * q.z;
        return {
            1.0f - 2.0f * (yy + zz), 2.0f * (xy - wz),        2.0f * (xz + wy),
            2.0f * (xy + wz),        1.0f - 2.0f * (xx + zz), 2.0f * (yz - wx),
            2.0f * (xz - wy),        2.0f * (yz + wx),        1.0f - 2.0f * (xx + yy),
            pos.x,                   pos.y,                   pos.z
        };
    }

    static Quat slerp(const Quat& qa, const Quat& qb, float t) noexcept {
        Quat a = qa.normalize();
        Quat b = qb.normalize();
        float cos_theta = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
        if (cos_theta < 0.0f) {
            b = {-b.x, -b.y, -b.z, -b.w};
            cos_theta = -cos_theta;
        }
        if (cos_theta > 0.9995f) {
            return Quat{
                a.x + (b.x - a.x) * t,
                a.y + (b.y - a.y) * t,
                a.z + (b.z - a.z) * t,
                a.w + (b.w - a.w) * t
            }.normalize();
        }
        const float theta = std::acos(std::clamp(cos_theta, -1.0f, 1.0f));
        const float sin_theta = std::sin(theta);
        const float wa = std::sin((1.0f - t) * theta) / sin_theta;
        const float wb = std::sin(t * theta) / sin_theta;
        return Quat{
            a.x * wa + b.x * wb,
            a.y * wa + b.y * wb,
            a.z * wa + b.z * wb,
            a.w * wa + b.w * wb
        }.normalize();
    }
};

inline Mat3x4 interpolate_mat3x4(const Mat3x4& a, const Mat3x4& b, float t) noexcept {
    t = std::clamp(t, 0.0f, 1.0f);
    if (t <= 0.0f || !is_valid_mat3x4(a) || !is_valid_mat3x4(b)) return a;
    if (t >= 1.0f) return b;
    const Vec3 pa = mat_pos(a);
    const Vec3 pb = mat_pos(b);
    if (length_sq(pb - pa) > 2500.0f) return a; // teleport guard (> 50m in 1 frame)
    const Vec3 p = lerp(pa, pb, t);
    const Quat qa = Quat::from_mat3x4(a);
    const Quat qb = Quat::from_mat3x4(b);
    return Quat::slerp(qa, qb, t).to_mat3x4(p);
}

// 6-DOF Free-Fly Camera Controller
struct FreeFlyCamera {
    Vec3 pos{0.f, 10.f, 0.f};
    float pitch_rad{0.f};
    float yaw_rad{0.f};
    float roll_rad{0.f};
    float fov_deg{60.f};
    float default_fov_deg{60.f};
    float move_speed{45.f};
    float look_sensitivity{0.0028f};

    void sync_from_game(const Mat3x4& m, float game_vfov_deg) noexcept {
        if (is_valid_mat3x4(m)) {
            pos = mat_pos(m);
            mat3x4_to_euler(m, pitch_rad, yaw_rad, roll_rad);
        }
        if (std::isfinite(game_vfov_deg) && game_vfov_deg >= 10.f && game_vfov_deg <= 120.f) {
            fov_deg = game_vfov_deg;
            default_fov_deg = game_vfov_deg;
        }
    }

    void init_from_matrix(const Mat3x4& m, float game_vfov_deg) noexcept {
        sync_from_game(m, game_vfov_deg);
    }

    void reset_roll_and_fov(float fallback_fov_deg = -1.0f) noexcept {
        roll_rad = 0.0f;
        fov_deg = (fallback_fov_deg > 0.0f) ? fallback_fov_deg : default_fov_deg;
    }

    void adjust_fov(float delta_deg) noexcept {
        fov_deg = std::clamp(fov_deg + delta_deg, 10.0f, 120.0f);
    }

    void adjust_speed(float factor) noexcept {
        move_speed = std::clamp(move_speed * factor, 2.0f, 500.0f);
    }

    void step(float dt, float move_forward, float move_right, float move_up,
              float mouse_dx, float mouse_dy, float roll_dir, float speed_mult = 1.0f) noexcept {
        const float max_pitch = 89.0f * kDegToRad;
        yaw_rad -= mouse_dx * look_sensitivity;
        pitch_rad = std::clamp(pitch_rad - mouse_dy * look_sensitivity, -max_pitch, max_pitch);
        roll_rad += roll_dir * 1.4f * dt;

        const Mat3x4 m = to_matrix();
        const Vec3 fwd = mat_forward(m);
        const Vec3 rgt = mat_right(m);
        const Vec3 up{0.0f, 1.0f, 0.0f};

        const float v = move_speed * speed_mult * dt;
        pos += fwd * (move_forward * v) + rgt * (move_right * v) + up * (move_up * v);
    }

    Mat3x4 to_matrix() const noexcept {
        return euler_to_mat3x4(pitch_rad, yaw_rad, roll_rad, pos);
    }
};

// Orbit Target Camera Controller
struct OrbitCamera {
    Vec3 target_center{0.f, 6.f, 0.f};
    float azimuth_rad{0.f};
    float elevation_rad{0.25f};
    float radius{28.f};
    float roll_rad{0.f};
    float fov_deg{60.f};
    Vec3 pan_offset{0.f, 0.f, 0.f};

    void init_from_pose(const Vec3& target, const Vec3& cam_pos, float current_fov_deg, float initial_yaw_rad = 0.0f) noexcept {
        target_center = target;
        pan_offset = {0.f, 0.f, 0.f};
        fov_deg = std::clamp(current_fov_deg, 10.f, 120.f);
        const Vec3 diff = cam_pos - target;
        const float dist = length(diff);
        if (dist >= 8.0f && std::isfinite(dist)) {
            radius = std::clamp(dist, 4.0f, 400.0f);
            elevation_rad = std::clamp(std::asin(std::clamp(diff.y / dist, -0.98f, 0.98f)), -1.45f, 1.45f);
            azimuth_rad = std::atan2(diff.x, diff.z);
        } else {
            radius = 28.0f;
            elevation_rad = 0.25f;
            azimuth_rad = std::isfinite(initial_yaw_rad) ? initial_yaw_rad : 0.0f;
        }
    }

    void step(float dt, float orbit_dx, float orbit_dy, float dolly_in,
              float pan_right, float pan_up, float roll_dir) noexcept {
        azimuth_rad -= orbit_dx * 0.0045f;
        elevation_rad = std::clamp(elevation_rad + orbit_dy * 0.0045f, -1.48f, 1.48f);
        radius = std::clamp(radius - dolly_in * 28.0f * dt, 2.5f, 500.0f);
        roll_rad += roll_dir * 1.4f * dt;

        const Mat3x4 m = to_matrix();
        pan_offset += mat_right(m) * (pan_right * 15.0f * dt) + mat_up(m) * (pan_up * 15.0f * dt);
    }

    Mat3x4 to_matrix() const noexcept {
        const float ce = std::cos(elevation_rad), se = std::sin(elevation_rad);
        const float ca = std::cos(azimuth_rad),   sa = std::sin(azimuth_rad);
        const Vec3 pivot = target_center + pan_offset;
        const Vec3 offset{sa * ce * radius, se * radius, ca * ce * radius};
        const Vec3 pos = pivot + offset;
        return euler_to_mat3x4(-elevation_rad, azimuth_rad, roll_rad, pos);
    }
};

// Catmull-Rom + Slerp Camera Path Keyframe & Spline Evaluator
struct DollyKeyframe {
    float time_sec{};
    Vec3 pos{};
    Quat rot{};
    float fov_deg{60.f};
};

struct DollySpline {
    std::vector<DollyKeyframe> keyframes;
    bool playing{};
    bool loop{true};
    float playhead_sec{};
    float duration_sec{};

    void clear() noexcept {
        keyframes.clear();
        playing = false;
        playhead_sec = 0.0f;
        duration_sec = 0.0f;
    }

    void add_keyframe(const Mat3x4& m, float fov_deg, float spacing_sec = 2.5f) {
        const float t = keyframes.empty() ? 0.0f : (keyframes.back().time_sec + spacing_sec);
        keyframes.push_back({t, mat_pos(m), Quat::from_mat3x4(m), std::clamp(fov_deg, 10.f, 120.f)});
        duration_sec = keyframes.back().time_sec;
    }

    void remove_last() noexcept {
        if (!keyframes.empty()) keyframes.pop_back();
        duration_sec = keyframes.empty() ? 0.0f : keyframes.back().time_sec;
        if (playhead_sec > duration_sec) playhead_sec = duration_sec;
        if (keyframes.size() < 2) playing = false;
    }

    static Vec3 catmull_rom(const Vec3& p0, const Vec3& p1, const Vec3& p2, const Vec3& p3, float t) noexcept {
        const float t2 = t * t;
        const float t3 = t2 * t;
        return (p1 * 2.0f +
                (p2 - p0) * t +
                (p0 * 2.0f - p1 * 5.0f + p2 * 4.0f - p3) * t2 +
                (p1 * 3.0f - p0 - p2 * 3.0f + p3) * t3) * 0.5f;
    }

    bool evaluate(float t_sec, Mat3x4& out_mat, float& out_fov_deg) const noexcept {
        if (keyframes.empty()) return false;
        if (keyframes.size() == 1) {
            out_mat = keyframes[0].rot.to_mat3x4(keyframes[0].pos);
            out_fov_deg = keyframes[0].fov_deg;
            return true;
        }
        const float clamped_t = std::clamp(t_sec, keyframes.front().time_sec, keyframes.back().time_sec);
        std::size_t seg = 0;
        for (std::size_t i = 0; i + 1 < keyframes.size(); ++i) {
            if (clamped_t >= keyframes[i].time_sec && clamped_t <= keyframes[i + 1].time_sec) {
                seg = i;
                break;
            }
        }
        const auto& k1 = keyframes[seg];
        const auto& k2 = keyframes[seg + 1];
        const auto& k0 = seg > 0 ? keyframes[seg - 1] : k1;
        const auto& k3 = (seg + 2 < keyframes.size()) ? keyframes[seg + 2] : k2;

        const float span = std::max(1e-4f, k2.time_sec - k1.time_sec);
        const float u = std::clamp((clamped_t - k1.time_sec) / span, 0.0f, 1.0f);
        // Smoothstep easing at endpoints when only 2 keyframes exist
        const Vec3 pos = catmull_rom(k0.pos, k1.pos, k2.pos, k3.pos, u);
        const Quat rot = Quat::slerp(k1.rot, k2.rot, u);
        out_mat = rot.to_mat3x4(pos);
        out_fov_deg = k1.fov_deg + (k2.fov_deg - k1.fov_deg) * u;
        return true;
    }
};

// 64-byte Cacheline Delta inside a 4 KB page for < 1 ms instant Replay seeking
struct PageBlockDelta {
    std::uint32_t page_va{};
    std::uint64_t line_mask{}; // 1 bit per 64-byte cacheline in the 4096-byte page
    std::uint32_t data_offset{};
};

struct NodeTransformSample {
    std::uint32_t data_va{};
    Mat3x4 mat{};
};

struct OrbitTargetSample {
    std::uint32_t root_va{};
    Vec3 pos{};
    char label[24]{};
};

// Device state lives in the host provider, outside the guest memory pages.
// It must travel with the guest's cached state setters when a frame is restored.
struct ReplayDeviceState {
    std::uint32_t guest{}, viewport{};
    std::array<std::uint32_t, 256> render_states{};
    std::array<std::array<std::uint32_t, 32>, 8> texture_states{};
    std::array<std::uint32_t, 8> textures{};
};
struct ReplayViewportState {
    std::uint32_t guest{}, background{}, set{};
    std::array<std::uint32_t, 11> words{};
};

// Bounded host presentation metadata, never native pointers or graphics handles.
struct ReplayHeadlightState {
    std::uint32_t actor{}, root{}, chassis{}, desired{};
    std::uint64_t generation{};
    float intensity{};
    std::uint32_t retired_mask{};
};
struct ReplayFrameRecord {
    std::vector<ReplayHeadlightState> headlights;
    std::uint32_t frame_index{};
    std::uint32_t guest_tick_ms{};
    float mission_time_sec{};
    float dt_sec{};
    Mat3x4 game_cam_mat{identity_mat3x4()};
    float game_cam_vfov_deg{60.f};
    std::uint32_t gheap_top{};
    std::uint32_t gheap_mapped{};
    std::uint32_t gheap_region_end{};
    std::uint64_t gheap_allocs{};
    std::uint64_t gheap_frees{};
    std::vector<std::pair<std::uint32_t, std::uint32_t>> gheap_free_blocks;
    std::vector<std::pair<std::uint32_t, std::uint32_t>> gheap_live;
    std::vector<std::pair<std::uint32_t, std::uint32_t>> gheap_regions;
    std::vector<std::pair<std::uint32_t, std::uint32_t>> gheap_region_owners;
    std::vector<ReplayDeviceState> graphics_devices;
    std::vector<ReplayViewportState> graphics_viewports;
    std::vector<PageBlockDelta> page_deltas;
    std::vector<std::uint8_t> delta_bytes; // 64 bytes per set bit in page_deltas
    std::vector<NodeTransformSample> node_poses;
    std::vector<OrbitTargetSample> orbit_targets;
};

struct ReplayCheckpoint {
    std::uint32_t frame_index{};
    // Full 4 KB pages that differ from base_pages_ at this checkpoint
    std::vector<std::uint32_t> diff_page_vas;
    std::vector<std::uint8_t> diff_page_bytes; // 4096 bytes per entry in diff_page_vas
};

class PageDeltaReplayBuffer {
public:
    static constexpr std::uint32_t kPageSize = 4096;
    static constexpr std::uint32_t kCachelineSize = 64;
    static constexpr std::uint32_t kCheckpointInterval = 60;

    void clear() {
        initialized_ = false;
        tracked_pages_.clear();
        page_index_map_.clear();
        base_pages_.clear();
        shadow_pages_.clear();
        frames_.clear();
        checkpoints_.clear();
    }

    bool empty() const noexcept { return frames_.empty(); }
    std::size_t frame_count() const noexcept { return frames_.size(); }

    const ReplayFrameRecord& frame(std::size_t idx) const { return frames_.at(idx); }
    const std::vector<ReplayFrameRecord>& frames() const noexcept { return frames_; }

    float total_duration_sec() const noexcept {
        if (frames_.size() < 2) return 0.0f;
        return std::max(0.0f, frames_.back().mission_time_sec - frames_.front().mission_time_sec);
    }

    std::size_t find_frame_by_time(float relative_sec) const noexcept {
        if (frames_.empty()) return 0;
        const float target_t = frames_.front().mission_time_sec + std::max(0.0f, relative_sec);
        std::size_t lo = 0, hi = frames_.size() - 1;
        while (lo < hi) {
            const std::size_t mid = (lo + hi + 1) / 2;
            if (frames_[mid].mission_time_sec <= target_t) lo = mid;
            else hi = mid - 1;
        }
        return lo;
    }

    void ensure_page_tracked(std::uint32_t page_va, const std::uint8_t* initial_bytes) {
        page_va &= ~(kPageSize - 1U);
        if (page_index_map_.find(page_va) != page_index_map_.end()) return;
        const std::uint32_t idx = static_cast<std::uint32_t>(tracked_pages_.size());
        tracked_pages_.push_back(page_va);
        page_index_map_.emplace(page_va, idx);
        const std::size_t old_sz = base_pages_.size();
        base_pages_.resize(old_sz + kPageSize);
        shadow_pages_.resize(old_sz + kPageSize);
        std::memcpy(base_pages_.data() + old_sz, initial_bytes, kPageSize);
        std::memcpy(shadow_pages_.data() + old_sz, initial_bytes, kPageSize);
        initialized_ = true;
    }

    // Record a new frame from the current flat guest memory base and candidate page ranges
    void record_frame(const std::uint8_t* flat_base,
                      const std::vector<std::pair<std::uint32_t, std::uint32_t>>& ranges,
                      const std::vector<std::uint32_t>* dirty_hint_pages,
                      ReplayFrameRecord&& meta,
                      std::size_t max_frames = 18000) {
        if (!flat_base) return;
        if (frames_.size() >= max_frames) {
            // Trim oldest checkpoint window (60 frames) and rebase
            trim_oldest_window();
        }
        for (const auto& [lo, hi] : ranges) {
            for (std::uint32_t p = lo & ~(kPageSize - 1U); p < hi; p += kPageSize) {
                ensure_page_tracked(p, flat_base + p);
            }
        }

        const std::uint32_t f_idx = static_cast<std::uint32_t>(frames_.size());
        meta.frame_index = f_idx;
        meta.page_deltas.clear();
        meta.delta_bytes.clear();

        auto process_page = [&](std::uint32_t page_va, std::uint32_t idx) {
            const std::uint8_t* cur = flat_base + page_va;
            std::uint8_t* shd = shadow_pages_.data() + std::size_t(idx) * kPageSize;
            if (std::memcmp(cur, shd, kPageSize) == 0) return;

            std::uint64_t mask = 0;
            for (unsigned line = 0; line < 64; ++line) {
                if (std::memcmp(cur + line * kCachelineSize, shd + line * kCachelineSize, kCachelineSize) != 0) {
                    mask |= (std::uint64_t{1} << line);
                }
            }
            if (!mask) return;
            const std::uint32_t off = static_cast<std::uint32_t>(meta.delta_bytes.size());
            meta.page_deltas.push_back({page_va, mask, off});
            for (unsigned line = 0; line < 64; ++line) {
                if (mask & (std::uint64_t{1} << line)) {
                    const std::uint8_t* src_line = cur + line * kCachelineSize;
                    meta.delta_bytes.insert(meta.delta_bytes.end(), src_line, src_line + kCachelineSize);
                    std::memcpy(shd + line * kCachelineSize, src_line, kCachelineSize);
                }
            }
        };

        if (dirty_hint_pages && !dirty_hint_pages->empty() && f_idx > 0) {
            for (std::uint32_t p : *dirty_hint_pages) {
                auto it = page_index_map_.find(p & ~(kPageSize - 1U));
                if (it != page_index_map_.end()) process_page(it->first, it->second);
            }
        } else {
            for (std::uint32_t idx = 0; idx < tracked_pages_.size(); ++idx) {
                process_page(tracked_pages_[idx], idx);
            }
        }

        if (f_idx % kCheckpointInterval == 0) {
            ReplayCheckpoint cp{};
            cp.frame_index = f_idx;
            for (std::uint32_t idx = 0; idx < tracked_pages_.size(); ++idx) {
                const std::uint8_t* shd = shadow_pages_.data() + std::size_t(idx) * kPageSize;
                const std::uint8_t* bas = base_pages_.data() + std::size_t(idx) * kPageSize;
                if (std::memcmp(shd, bas, kPageSize) != 0) {
                    cp.diff_page_vas.push_back(tracked_pages_[idx]);
                    cp.diff_page_bytes.insert(cp.diff_page_bytes.end(), shd, shd + kPageSize);
                }
            }
            checkpoints_.push_back(std::move(cp));
        }

        frames_.push_back(std::move(meta));
    }

    // Reconstruct exact guest memory at target_frame into flat_base in < 1 ms
    bool restore_frame(std::size_t target_frame, std::uint8_t* flat_base) {
        if (!initialized_ || frames_.empty() || !flat_base) return false;
        if (target_frame >= frames_.size()) target_frame = frames_.size() - 1;

        // 1. Reset shadow_pages_ to base_pages_
        std::memcpy(shadow_pages_.data(), base_pages_.data(), base_pages_.size());

        // 2. Find nearest checkpoint <= target_frame
        std::size_t start_frame = 0;
        if (!checkpoints_.empty()) {
            std::size_t cp_idx = 0;
            for (std::size_t i = 0; i < checkpoints_.size(); ++i) {
                if (checkpoints_[i].frame_index <= target_frame) cp_idx = i;
                else break;
            }
            const auto& cp = checkpoints_[cp_idx];
            start_frame = cp.frame_index + 1;
            for (std::size_t i = 0; i < cp.diff_page_vas.size(); ++i) {
                auto it = page_index_map_.find(cp.diff_page_vas[i]);
                if (it != page_index_map_.end()) {
                    std::memcpy(shadow_pages_.data() + std::size_t(it->second) * kPageSize,
                                cp.diff_page_bytes.data() + i * kPageSize, kPageSize);
                }
            }
        }

        // 3. Apply incremental cacheline deltas from start_frame .. target_frame
        for (std::size_t f = start_frame; f <= target_frame; ++f) {
            const auto& rec = frames_[f];
            for (const auto& pd : rec.page_deltas) {
                auto it = page_index_map_.find(pd.page_va);
                if (it == page_index_map_.end()) continue;
                std::uint8_t* shd = shadow_pages_.data() + std::size_t(it->second) * kPageSize;
                std::uint32_t off = pd.data_offset;
                for (unsigned line = 0; line < 64; ++line) {
                    if (pd.line_mask & (std::uint64_t{1} << line)) {
                        if (off + kCachelineSize <= rec.delta_bytes.size()) {
                            std::memcpy(shd + line * kCachelineSize, rec.delta_bytes.data() + off, kCachelineSize);
                            off += kCachelineSize;
                        }
                    }
                }
            }
        }

        // 4. Write modified pages back to flat_base
        for (std::uint32_t idx = 0; idx < tracked_pages_.size(); ++idx) {
            const std::uint32_t page_va = tracked_pages_[idx];
            const std::uint8_t* shd = shadow_pages_.data() + std::size_t(idx) * kPageSize;
            std::uint8_t* dst = flat_base + page_va;
            if (std::memcmp(dst, shd, kPageSize) != 0) {
                std::memcpy(dst, shd, kPageSize);
            }
        }
        return true;
    }

    // Save entire replay buffer to disk (.mw3replay binary format)
    bool save_to_file(const std::string& path) const {
        if (!initialized_ || frames_.empty()) return false;
        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        if (!out) return false;

        auto wr = [&](const void* p, std::size_t n) {
            out.write(reinterpret_cast<const char*>(p), static_cast<std::streamsize>(n));
        };
        auto wr_u32 = [&](std::uint32_t v) { wr(&v, 4); };
        auto wr_u64 = [&](std::uint64_t v) { wr(&v, 8); };
        auto wr_f32 = [&](float v) { wr(&v, 4); };

        const char magic[8] = {'M', 'W', '3', 'R', 'P', 'L', 'Y', '4'};
        wr(magic, 8);
        wr_u32(static_cast<std::uint32_t>(tracked_pages_.size()));
        wr_u32(static_cast<std::uint32_t>(frames_.size()));
        wr_u32(static_cast<std::uint32_t>(checkpoints_.size()));

        if (!tracked_pages_.empty()) {
            wr(tracked_pages_.data(), tracked_pages_.size() * 4);
            wr(base_pages_.data(), base_pages_.size());
        }

        for (const auto& cp : checkpoints_) {
            wr_u32(cp.frame_index);
            wr_u32(static_cast<std::uint32_t>(cp.diff_page_vas.size()));
            if (!cp.diff_page_vas.empty()) {
                wr(cp.diff_page_vas.data(), cp.diff_page_vas.size() * 4);
                wr(cp.diff_page_bytes.data(), cp.diff_page_bytes.size());
            }
        }

        for (const auto& f : frames_) {
            wr_u32(f.frame_index);
            wr_u32(f.guest_tick_ms);
            wr_f32(f.mission_time_sec);
            wr_f32(f.dt_sec);
            wr(f.game_cam_mat.data(), 48);
            wr_f32(f.game_cam_vfov_deg);
            wr_u32(f.gheap_top);
            wr_u32(f.gheap_mapped);
            wr_u32(f.gheap_region_end);
            wr_u64(f.gheap_allocs);
            wr_u64(f.gheap_frees);

            auto wr_pairs = [&](const std::vector<std::pair<std::uint32_t, std::uint32_t>>& v) {
                wr_u32(static_cast<std::uint32_t>(v.size()));
                for (const auto& [a, b] : v) { wr_u32(a); wr_u32(b); }
            };
            wr_pairs(f.gheap_free_blocks);
            wr_pairs(f.gheap_live);
            wr_pairs(f.gheap_regions);
            wr_pairs(f.gheap_region_owners);

            wr_u32(static_cast<std::uint32_t>(f.graphics_devices.size()));
            for (const auto& d : f.graphics_devices) {
                wr_u32(d.guest); wr_u32(d.viewport);
                wr(d.render_states.data(), sizeof(d.render_states));
                wr(d.texture_states.data(), sizeof(d.texture_states));
                wr(d.textures.data(), sizeof(d.textures));
            }
            wr_u32(static_cast<std::uint32_t>(f.graphics_viewports.size()));
            for (const auto& v : f.graphics_viewports) {
                wr_u32(v.guest); wr_u32(v.background); wr_u32(v.set);
                wr(v.words.data(), sizeof(v.words));
            }

            wr_u32(static_cast<std::uint32_t>(f.page_deltas.size()));
            for (const auto& pd : f.page_deltas) {
                wr_u32(pd.page_va);
                wr_u64(pd.line_mask);
                wr_u32(pd.data_offset);
            }
            wr_u32(static_cast<std::uint32_t>(f.delta_bytes.size()));
            if (!f.delta_bytes.empty()) wr(f.delta_bytes.data(), f.delta_bytes.size());

            wr_u32(static_cast<std::uint32_t>(f.node_poses.size()));
            if (!f.node_poses.empty()) wr(f.node_poses.data(), f.node_poses.size() * sizeof(NodeTransformSample));

            wr_u32(static_cast<std::uint32_t>(f.orbit_targets.size()));
            if (!f.orbit_targets.empty()) wr(f.orbit_targets.data(), f.orbit_targets.size() * sizeof(OrbitTargetSample));
            if (f.headlights.size() > 1024) return false;
            wr_u32(static_cast<std::uint32_t>(f.headlights.size()));
            for (const auto& lamp : f.headlights) {
                wr_u32(lamp.actor); wr_u32(lamp.root); wr_u32(lamp.chassis); wr_u32(lamp.desired);
                wr_u64(lamp.generation); wr_f32(lamp.intensity); wr_u32(lamp.retired_mask);
            }
        }

        return static_cast<bool>(out);
    }

    bool load_from_file(const std::string& path) {
        std::ifstream in(path, std::ios::binary);
        if (!in) return false;

        auto rd = [&](void* p, std::size_t n) -> bool {
            return static_cast<bool>(in.read(reinterpret_cast<char*>(p), static_cast<std::streamsize>(n)));
        };
        auto rd_u32 = [&](std::uint32_t& v) { return rd(&v, 4); };
        auto rd_u64 = [&](std::uint64_t& v) { return rd(&v, 8); };
        auto rd_f32 = [&](float& v) { return rd(&v, 4); };

        char magic[8]{};
        if (!rd(magic, 8)) return false;
        const bool headlights = std::memcmp(magic, "MW3RPLY4", 8) == 0;
        if (!headlights && std::memcmp(magic, "MW3RPLY3", 8) != 0) return false;

        std::uint32_t num_pages = 0, num_frames = 0, num_cps = 0;
        if (!rd_u32(num_pages) || !rd_u32(num_frames) || !rd_u32(num_cps)) return false;
        if (num_pages > 262144 || num_frames == 0 || num_frames > 100000) return false;

        clear();
        tracked_pages_.resize(num_pages);
        if (num_pages > 0) {
            if (!rd(tracked_pages_.data(), std::size_t(num_pages) * 4)) { clear(); return false; }
            base_pages_.resize(std::size_t(num_pages) * kPageSize);
            shadow_pages_.resize(base_pages_.size());
            if (!rd(base_pages_.data(), base_pages_.size())) { clear(); return false; }
            std::memcpy(shadow_pages_.data(), base_pages_.data(), base_pages_.size());
            for (std::uint32_t i = 0; i < num_pages; ++i) {
                page_index_map_.emplace(tracked_pages_[i], i);
            }
        }

        checkpoints_.resize(num_cps);
        for (std::uint32_t i = 0; i < num_cps; ++i) {
            auto& cp = checkpoints_[i];
            std::uint32_t n_diff = 0;
            if (!rd_u32(cp.frame_index) || !rd_u32(n_diff) || n_diff > num_pages) { clear(); return false; }
            cp.diff_page_vas.resize(n_diff);
            cp.diff_page_bytes.resize(std::size_t(n_diff) * kPageSize);
            if (n_diff > 0) {
                if (!rd(cp.diff_page_vas.data(), std::size_t(n_diff) * 4) ||
                    !rd(cp.diff_page_bytes.data(), cp.diff_page_bytes.size())) {
                    clear();
                    return false;
                }
            }
        }

        frames_.resize(num_frames);
        for (std::uint32_t i = 0; i < num_frames; ++i) {
            auto& f = frames_[i];
            if (!rd_u32(f.frame_index) || !rd_u32(f.guest_tick_ms) ||
                !rd_f32(f.mission_time_sec) || !rd_f32(f.dt_sec) ||
                !rd(f.game_cam_mat.data(), 48) || !rd_f32(f.game_cam_vfov_deg) ||
                !rd_u32(f.gheap_top) || !rd_u32(f.gheap_mapped) || !rd_u32(f.gheap_region_end) ||
                !rd_u64(f.gheap_allocs) || !rd_u64(f.gheap_frees)) {
                clear();
                return false;
            }

            auto rd_pairs = [&](std::vector<std::pair<std::uint32_t, std::uint32_t>>& v) -> bool {
                std::uint32_t cnt = 0;
                if (!rd_u32(cnt) || cnt > 262144) return false;
                v.resize(cnt);
                for (std::uint32_t k = 0; k < cnt; ++k) {
                    if (!rd_u32(v[k].first) || !rd_u32(v[k].second)) return false;
                }
                return true;
            };
            if (!rd_pairs(f.gheap_free_blocks) || !rd_pairs(f.gheap_live) || !rd_pairs(f.gheap_regions) || !rd_pairs(f.gheap_region_owners)) {
                clear();
                return false;
            }

            std::uint32_t n_devices = 0, n_viewports = 0;
            if (!rd_u32(n_devices) || n_devices > 64) { clear(); return false; }
            f.graphics_devices.resize(n_devices);
            for (auto& d : f.graphics_devices) {
                if (!rd_u32(d.guest) || !rd_u32(d.viewport) ||
                    !rd(d.render_states.data(), sizeof(d.render_states)) ||
                    !rd(d.texture_states.data(), sizeof(d.texture_states)) ||
                    !rd(d.textures.data(), sizeof(d.textures))) { clear(); return false; }
            }
            if (!rd_u32(n_viewports) || n_viewports > 256) { clear(); return false; }
            f.graphics_viewports.resize(n_viewports);
            for (auto& v : f.graphics_viewports) {
                if (!rd_u32(v.guest) || !rd_u32(v.background) || !rd_u32(v.set) || v.set > 1 ||
                    !rd(v.words.data(), sizeof(v.words))) { clear(); return false; }
            }

            std::uint32_t n_pd = 0;
            if (!rd_u32(n_pd) || n_pd > num_pages) { clear(); return false; }
            f.page_deltas.resize(n_pd);
            for (std::uint32_t k = 0; k < n_pd; ++k) {
                if (!rd_u32(f.page_deltas[k].page_va) ||
                    !rd_u64(f.page_deltas[k].line_mask) ||
                    !rd_u32(f.page_deltas[k].data_offset)) {
                    clear();
                    return false;
                }
            }
            std::uint32_t n_db = 0;
            if (!rd_u32(n_db) || n_db > num_pages * kPageSize) { clear(); return false; }
            f.delta_bytes.resize(n_db);
            if (n_db > 0 && !rd(f.delta_bytes.data(), n_db)) { clear(); return false; }

            std::uint32_t n_np = 0;
            if (!rd_u32(n_np) || n_np > 16384) { clear(); return false; }
            f.node_poses.resize(n_np);
            if (n_np > 0 && !rd(f.node_poses.data(), std::size_t(n_np) * sizeof(NodeTransformSample))) {
                clear();
                return false;
            }

            std::uint32_t n_ot = 0;
            if (!rd_u32(n_ot) || n_ot > 1024) { clear(); return false; }
            f.orbit_targets.resize(n_ot);
            if (n_ot > 0 && !rd(f.orbit_targets.data(), std::size_t(n_ot) * sizeof(OrbitTargetSample))) {
                clear();
                return false;
            }
            if (headlights) {
                std::uint32_t count{};
                if (!rd_u32(count) || count > 1024) { clear(); return false; }
                f.headlights.resize(count);
                std::set<std::uint32_t> actors;
                for (auto& lamp : f.headlights) {
                    if (!rd_u32(lamp.actor) || !rd_u32(lamp.root) || !rd_u32(lamp.chassis) ||
                        !rd_u32(lamp.desired) || !rd_u64(lamp.generation) || !rd_f32(lamp.intensity) ||
                        !rd_u32(lamp.retired_mask) || lamp.retired_mask > 255 ||
                        !lamp.actor || !lamp.root || !lamp.generation || lamp.chassis >= 128 || lamp.desired > 1 ||
                        !std::isfinite(lamp.intensity) || lamp.intensity < 0 || lamp.intensity > 1 ||
                        !actors.insert(lamp.actor).second) { clear(); return false; }
                }
            }
        }

        initialized_ = true;
        return true;
    }

private:
    void trim_oldest_window() {
        if (frames_.size() <= kCheckpointInterval || checkpoints_.size() < 2) return;
        // Advance base_pages_ to checkpoints_[1] (frame kCheckpointInterval)
        const auto& cp1 = checkpoints_[1];
        for (std::size_t i = 0; i < cp1.diff_page_vas.size(); ++i) {
            auto it = page_index_map_.find(cp1.diff_page_vas[i]);
            if (it != page_index_map_.end()) {
                std::memcpy(base_pages_.data() + std::size_t(it->second) * kPageSize,
                            cp1.diff_page_bytes.data() + i * kPageSize, kPageSize);
            }
        }
        frames_.erase(frames_.begin(), frames_.begin() + kCheckpointInterval);
        for (std::size_t i = 0; i < frames_.size(); ++i) {
            frames_[i].frame_index = static_cast<std::uint32_t>(i);
        }
        checkpoints_.erase(checkpoints_.begin());
        for (auto& cp : checkpoints_) {
            cp.frame_index -= kCheckpointInterval;
        }
    }

    bool initialized_{};
    std::vector<std::uint32_t> tracked_pages_;
    std::unordered_map<std::uint32_t, std::uint32_t> page_index_map_;
    std::vector<std::uint8_t> base_pages_;
    std::vector<std::uint8_t> shadow_pages_;
    std::vector<ReplayFrameRecord> frames_;
    std::vector<ReplayCheckpoint> checkpoints_;
};

// Self-contained Lossless PNG Encoder (RGB24 -> PNG)
inline std::uint32_t crc32_update(std::uint32_t crc, const std::uint8_t* buf, std::size_t len) noexcept {
    static const std::array<std::uint32_t, 256> table = [] {
        std::array<std::uint32_t, 256> t{};
        for (std::uint32_t i = 0; i < 256; ++i) {
            std::uint32_t c = i;
            for (int k = 0; k < 8; ++k) c = (c & 1) ? (0xEDB88320U ^ (c >> 1)) : (c >> 1);
            t[i] = c;
        }
        return t;
    }();
    std::uint32_t c = crc ^ 0xFFFFFFFFU;
    for (std::size_t i = 0; i < len; ++i) c = table[(c ^ buf[i]) & 0xFFU] ^ (c >> 8);
    return c ^ 0xFFFFFFFFU;
}

inline std::vector<std::uint8_t> encode_png_rgb24(const std::uint8_t* rgb, unsigned width, unsigned height) {
    std::vector<std::uint8_t> out;
    if (!rgb || !width || !height) return out;

    auto push_u32_be = [&](std::vector<std::uint8_t>& v, std::uint32_t x) {
        v.push_back(static_cast<std::uint8_t>((x >> 24) & 0xFF));
        v.push_back(static_cast<std::uint8_t>((x >> 16) & 0xFF));
        v.push_back(static_cast<std::uint8_t>((x >> 8) & 0xFF));
        v.push_back(static_cast<std::uint8_t>(x & 0xFF));
    };
    auto push_chunk = [&](const char type[4], const std::uint8_t* data, std::size_t len) {
        push_u32_be(out, static_cast<std::uint32_t>(len));
        const std::size_t type_pos = out.size();
        out.insert(out.end(), reinterpret_cast<const std::uint8_t*>(type), reinterpret_cast<const std::uint8_t*>(type) + 4);
        if (len > 0 && data) out.insert(out.end(), data, data + len);
        const std::uint32_t crc = crc32_update(0, out.data() + type_pos, 4 + len);
        push_u32_be(out, crc);
    };

    const std::uint8_t sig[8] = {137, 80, 78, 71, 13, 10, 26, 10};
    out.insert(out.end(), sig, sig + 8);

    std::uint8_t ihdr[13]{};
    ihdr[0] = static_cast<std::uint8_t>((width >> 24) & 0xFF);
    ihdr[1] = static_cast<std::uint8_t>((width >> 16) & 0xFF);
    ihdr[2] = static_cast<std::uint8_t>((width >> 8) & 0xFF);
    ihdr[3] = static_cast<std::uint8_t>(width & 0xFF);
    ihdr[4] = static_cast<std::uint8_t>((height >> 24) & 0xFF);
    ihdr[5] = static_cast<std::uint8_t>((height >> 16) & 0xFF);
    ihdr[6] = static_cast<std::uint8_t>((height >> 8) & 0xFF);
    ihdr[7] = static_cast<std::uint8_t>(height & 0xFF);
    ihdr[8] = 8; // bit depth = 8
    ihdr[9] = 2; // color type = 2 (Truecolor RGB)
    ihdr[10] = 0;
    ihdr[11] = 0;
    ihdr[12] = 0;
    push_chunk("IHDR", ihdr, 13);

    // Build raw filtered scanlines (Filter 0 = None per row)
    const std::size_t row_bytes = std::size_t(width) * 3;
    const std::size_t raw_size = (row_bytes + 1) * height;
    std::vector<std::uint8_t> zstream;
    zstream.reserve(raw_size + (raw_size / 65535 + 2) * 5 + 6);
    // zlib header (CMF=0x78, FLG=0x01)
    zstream.push_back(0x78);
    zstream.push_back(0x01);

    std::uint32_t s1 = 1, s2 = 0;
    auto adler_feed = [&](const std::uint8_t* p, std::size_t n) {
        std::size_t i = 0;
        while (i < n) {
            const std::size_t chunk = std::min<std::size_t>(n - i, 5552);
            for (std::size_t k = 0; k < chunk; ++k) {
                s1 += p[i + k];
                s2 += s1;
            }
            s1 %= 65521U;
            s2 %= 65521U;
            i += chunk;
        }
    };

    std::vector<std::uint8_t> raw_buf(raw_size);
    for (unsigned y = 0; y < height; ++y) {
        std::uint8_t* dst = raw_buf.data() + std::size_t(y) * (row_bytes + 1);
        dst[0] = 0; // filter = None
        std::memcpy(dst + 1, rgb + std::size_t(y) * row_bytes, row_bytes);
    }
    adler_feed(raw_buf.data(), raw_buf.size());

    std::size_t pos = 0;
    while (pos < raw_size) {
        const std::uint16_t bsize = static_cast<std::uint16_t>(std::min<std::size_t>(65535, raw_size - pos));
        const bool last = (pos + bsize >= raw_size);
        zstream.push_back(last ? 0x01 : 0x00);
        zstream.push_back(static_cast<std::uint8_t>(bsize & 0xFF));
        zstream.push_back(static_cast<std::uint8_t>((bsize >> 8) & 0xFF));
        const std::uint16_t nlen = static_cast<std::uint16_t>(~bsize);
        zstream.push_back(static_cast<std::uint8_t>(nlen & 0xFF));
        zstream.push_back(static_cast<std::uint8_t>((nlen >> 8) & 0xFF));
        zstream.insert(zstream.end(), raw_buf.data() + pos, raw_buf.data() + pos + bsize);
        pos += bsize;
    }
    push_u32_be(zstream, (s2 << 16) | s1);

    push_chunk("IDAT", zstream.data(), zstream.size());
    push_chunk("IEND", nullptr, 0);
    return out;
}

inline bool write_png_file(const std::string& path, const std::uint8_t* rgb, unsigned width, unsigned height) {
    const auto png = encode_png_rgb24(rgb, width, height);
    if (png.empty()) return false;
    std::ofstream f(path, std::ios::binary | std::ios::trunc);
    if (!f) return false;
    f.write(reinterpret_cast<const char*>(png.data()), static_cast<std::streamsize>(png.size()));
    return static_cast<bool>(f);
}

inline bool encode_and_save_png_bgra(const std::string& path, const std::uint8_t* bgra, unsigned width, unsigned height) {
    if (!bgra || !width || !height) return false;
    std::vector<std::uint8_t> rgb(std::size_t(width) * height * 3);
    for (std::size_t i = 0; i < std::size_t(width) * height; ++i) {
        rgb[i * 3 + 0] = bgra[i * 4 + 2]; // R
        rgb[i * 3 + 1] = bgra[i * 4 + 1]; // G
        rgb[i * 3 + 2] = bgra[i * 4 + 0]; // B
    }
    return write_png_file(path, rgb.data(), width, height);
}

// 5x7 ASCII Bitmap Font for On-Screen Hotkey Legend & Replay Scrubber Overlay
inline const std::uint8_t* glyph_5x7(char ch) noexcept {
    // Each glyph is 7 rows of 5-bit patterns (bit 4 = leftmost pixel, bit 0 = rightmost pixel)
    static constexpr std::uint8_t kSpace[7] = {0, 0, 0, 0, 0, 0, 0};
    if (ch >= 'a' && ch <= 'z') ch = static_cast<char>(ch - 'a' + 'A');
    switch (ch) {
        case 'A': { static constexpr std::uint8_t g[7]={0x0E,0x11,0x11,0x1F,0x11,0x11,0x11}; return g; }
        case 'B': { static constexpr std::uint8_t g[7]={0x1E,0x11,0x11,0x1E,0x11,0x11,0x1E}; return g; }
        case 'C': { static constexpr std::uint8_t g[7]={0x0E,0x11,0x10,0x10,0x10,0x11,0x0E}; return g; }
        case 'D': { static constexpr std::uint8_t g[7]={0x1E,0x11,0x11,0x11,0x11,0x11,0x1E}; return g; }
        case 'E': { static constexpr std::uint8_t g[7]={0x1F,0x10,0x10,0x1E,0x10,0x10,0x1F}; return g; }
        case 'F': { static constexpr std::uint8_t g[7]={0x1F,0x10,0x10,0x1E,0x10,0x10,0x10}; return g; }
        case 'G': { static constexpr std::uint8_t g[7]={0x0E,0x11,0x10,0x17,0x11,0x11,0x0F}; return g; }
        case 'H': { static constexpr std::uint8_t g[7]={0x11,0x11,0x11,0x1F,0x11,0x11,0x11}; return g; }
        case 'I': { static constexpr std::uint8_t g[7]={0x0E,0x04,0x04,0x04,0x04,0x04,0x0E}; return g; }
        case 'J': { static constexpr std::uint8_t g[7]={0x07,0x02,0x02,0x02,0x12,0x12,0x0C}; return g; }
        case 'K': { static constexpr std::uint8_t g[7]={0x11,0x12,0x14,0x18,0x14,0x12,0x11}; return g; }
        case 'L': { static constexpr std::uint8_t g[7]={0x10,0x10,0x10,0x10,0x10,0x10,0x1F}; return g; }
        case 'M': { static constexpr std::uint8_t g[7]={0x11,0x1B,0x15,0x15,0x11,0x11,0x11}; return g; }
        case 'N': { static constexpr std::uint8_t g[7]={0x11,0x19,0x15,0x13,0x11,0x11,0x11}; return g; }
        case 'O': { static constexpr std::uint8_t g[7]={0x0E,0x11,0x11,0x11,0x11,0x11,0x0E}; return g; }
        case 'P': { static constexpr std::uint8_t g[7]={0x1E,0x11,0x11,0x1E,0x10,0x10,0x10}; return g; }
        case 'Q': { static constexpr std::uint8_t g[7]={0x0E,0x11,0x11,0x11,0x15,0x12,0x0D}; return g; }
        case 'R': { static constexpr std::uint8_t g[7]={0x1E,0x11,0x11,0x1E,0x14,0x12,0x11}; return g; }
        case 'S': { static constexpr std::uint8_t g[7]={0x0F,0x10,0x10,0x0E,0x01,0x01,0x1E}; return g; }
        case 'T': { static constexpr std::uint8_t g[7]={0x1F,0x04,0x04,0x04,0x04,0x04,0x04}; return g; }
        case 'U': { static constexpr std::uint8_t g[7]={0x11,0x11,0x11,0x11,0x11,0x11,0x0E}; return g; }
        case 'V': { static constexpr std::uint8_t g[7]={0x11,0x11,0x11,0x11,0x11,0x0A,0x04}; return g; }
        case 'W': { static constexpr std::uint8_t g[7]={0x11,0x11,0x11,0x15,0x15,0x1B,0x11}; return g; }
        case 'X': { static constexpr std::uint8_t g[7]={0x11,0x11,0x0A,0x04,0x0A,0x11,0x11}; return g; }
        case 'Y': { static constexpr std::uint8_t g[7]={0x11,0x11,0x0A,0x04,0x04,0x04,0x04}; return g; }
        case 'Z': { static constexpr std::uint8_t g[7]={0x1F,0x01,0x02,0x04,0x08,0x10,0x1F}; return g; }
        case '0': { static constexpr std::uint8_t g[7]={0x0E,0x11,0x13,0x15,0x19,0x11,0x0E}; return g; }
        case '1': { static constexpr std::uint8_t g[7]={0x04,0x0C,0x04,0x04,0x04,0x04,0x0E}; return g; }
        case '2': { static constexpr std::uint8_t g[7]={0x0E,0x11,0x01,0x06,0x08,0x10,0x1F}; return g; }
        case '3': { static constexpr std::uint8_t g[7]={0x1F,0x02,0x04,0x06,0x01,0x11,0x0E}; return g; }
        case '4': { static constexpr std::uint8_t g[7]={0x02,0x06,0x0A,0x12,0x1F,0x02,0x02}; return g; }
        case '5': { static constexpr std::uint8_t g[7]={0x1F,0x10,0x1E,0x01,0x01,0x11,0x0E}; return g; }
        case '6': { static constexpr std::uint8_t g[7]={0x06,0x08,0x10,0x1E,0x11,0x11,0x0E}; return g; }
        case '7': { static constexpr std::uint8_t g[7]={0x1F,0x01,0x02,0x04,0x08,0x08,0x08}; return g; }
        case '8': { static constexpr std::uint8_t g[7]={0x0E,0x11,0x11,0x0E,0x11,0x11,0x0E}; return g; }
        case '9': { static constexpr std::uint8_t g[7]={0x0E,0x11,0x11,0x0F,0x01,0x02,0x0C}; return g; }
        case ':': { static constexpr std::uint8_t g[7]={0x00,0x04,0x04,0x00,0x04,0x04,0x00}; return g; }
        case '.': { static constexpr std::uint8_t g[7]={0x00,0x00,0x00,0x00,0x00,0x06,0x06}; return g; }
        case ',': { static constexpr std::uint8_t g[7]={0x00,0x00,0x00,0x00,0x06,0x04,0x08}; return g; }
        case '-': { static constexpr std::uint8_t g[7]={0x00,0x00,0x00,0x1F,0x00,0x00,0x00}; return g; }
        case '+': { static constexpr std::uint8_t g[7]={0x00,0x04,0x04,0x1F,0x04,0x04,0x00}; return g; }
        case '/': { static constexpr std::uint8_t g[7]={0x01,0x02,0x02,0x04,0x08,0x08,0x10}; return g; }
        case '[': { static constexpr std::uint8_t g[7]={0x0E,0x08,0x08,0x08,0x08,0x08,0x0E}; return g; }
        case ']': { static constexpr std::uint8_t g[7]={0x0E,0x02,0x02,0x02,0x02,0x02,0x0E}; return g; }
        case '(': { static constexpr std::uint8_t g[7]={0x02,0x04,0x08,0x08,0x08,0x04,0x02}; return g; }
        case ')': { static constexpr std::uint8_t g[7]={0x08,0x04,0x02,0x02,0x02,0x04,0x08}; return g; }
        case '<': { static constexpr std::uint8_t g[7]={0x02,0x04,0x08,0x10,0x08,0x04,0x02}; return g; }
        case '>': { static constexpr std::uint8_t g[7]={0x08,0x04,0x02,0x01,0x02,0x04,0x08}; return g; }
        case '|': { static constexpr std::uint8_t g[7]={0x04,0x04,0x04,0x04,0x04,0x04,0x04}; return g; }
        case '_': { static constexpr std::uint8_t g[7]={0x00,0x00,0x00,0x00,0x00,0x00,0x1F}; return g; }
        case '%': { static constexpr std::uint8_t g[7]={0x19,0x19,0x02,0x04,0x08,0x13,0x13}; return g; }
        case '#': { static constexpr std::uint8_t g[7]={0x0A,0x1F,0x0A,0x0A,0x1F,0x0A,0x00}; return g; }
        default: return kSpace;
    }
}

struct OverlayRenderState {
    Mode mode{Mode::Live};
    CameraMode camera_mode{CameraMode::Game};
    bool show_legend{true};
    bool paused{};
    bool hide_hud{};
    bool video_recording{};
    unsigned video_frames_captured{};
    float fov_deg{60.f};
    float fly_speed{45.f};
    float playback_speed{1.0f};
    float replay_cur_sec{0.0f};
    float replay_total_sec{0.0f};
    std::size_t replay_cur_frame{0};
    std::size_t replay_total_frames{0};
    std::size_t dolly_keyframes{0};
    bool dolly_playing{};
    std::string orbit_target_label;
    std::string status_banner;
};

inline void fill_rect_rgba(std::vector<std::uint32_t>& px, unsigned w, unsigned h,
                           int x0, int y0, int x1, int y1, std::uint32_t rgba) noexcept {
    x0 = std::clamp(x0, 0, int(w));
    y0 = std::clamp(y0, 0, int(h));
    x1 = std::clamp(x1, 0, int(w));
    y1 = std::clamp(y1, 0, int(h));
    for (int y = y0; y < y1; ++y) {
        std::uint32_t* row = px.data() + std::size_t(y) * w;
        for (int x = x0; x < x1; ++x) row[x] = rgba;
    }
}

inline void draw_text_rgba(std::vector<std::uint32_t>& px, unsigned w, unsigned h,
                           int x, int y, std::string_view text, std::uint32_t rgba, int scale = 1) noexcept {
    int cur_x = x;
    for (char c : text) {
        const std::uint8_t* g = glyph_5x7(c);
        for (int ry = 0; ry < 7; ++ry) {
            const std::uint8_t bits = g[ry];
            for (int rx = 0; rx < 5; ++rx) {
                if (bits & (1U << (4 - rx))) {
                    fill_rect_rgba(px, w, h,
                                   cur_x + rx * scale, y + ry * scale,
                                   cur_x + (rx + 1) * scale, y + (ry + 1) * scale,
                                   rgba);
                }
            }
        }
        cur_x += 6 * scale;
    }
}

// Builds an RGBA8888 overlay canvas (width x height) for the Hotkey Legend & Replay Scrubber.
// Returns false when nothing should be drawn on screen.
inline bool render_overlay_canvas(const OverlayRenderState& st, unsigned w, unsigned h,
                                  std::vector<std::uint32_t>& out_px) {
    const bool in_tool = (st.mode != Mode::Live) || (st.camera_mode != CameraMode::Game);
    const bool draw_legend_box = st.show_legend && in_tool;
    const bool draw_status_only = !draw_legend_box && (st.video_recording || !st.status_banner.empty());
    const bool draw_scrubber = (st.mode == Mode::Replay && st.replay_total_frames > 0 && st.show_legend);
    if (!draw_legend_box && !draw_status_only && !draw_scrubber) return false;
    if (!w || !h) return false;

    out_px.assign(std::size_t(w) * h, 0U);
    constexpr std::uint32_t kBgDark     = 0xCC14100CU; // ABGR (straight alpha RGBA8888 in memory)
    constexpr std::uint32_t kBgHeader   = 0xE6224414U;
    constexpr std::uint32_t kBorderGold = 0xFF38B8E8U;
    constexpr std::uint32_t kTextWhite  = 0xFFF2F6F8U;
    constexpr std::uint32_t kTextGold   = 0xFF40D8FFU;
    constexpr std::uint32_t kTextGreen  = 0xFF58F068U;
    constexpr std::uint32_t kTextCyan   = 0xFFF8E050U;
    constexpr std::uint32_t kRecRed     = 0xFF3030FFU;

    const int pad = 8;
    const int box_x0 = pad;
    const int box_y0 = pad;
    char line[128]{};

    if (draw_legend_box) {
        const int box_w  = std::min<int>(int(w) - 2 * pad, 340);
        const int box_h  = (st.mode == Mode::Replay) ? 178 : 148;

        // Panel background & border
        fill_rect_rgba(out_px, w, h, box_x0, box_y0, box_x0 + box_w, box_y0 + box_h, kBgDark);
        fill_rect_rgba(out_px, w, h, box_x0, box_y0, box_x0 + box_w, box_y0 + 16, kBgHeader);
        fill_rect_rgba(out_px, w, h, box_x0, box_y0, box_x0 + box_w, box_y0 + 1, kBorderGold);
        fill_rect_rgba(out_px, w, h, box_x0, box_y0 + box_h - 1, box_x0 + box_w, box_y0 + box_h, kBorderGold);
        fill_rect_rgba(out_px, w, h, box_x0, box_y0, box_x0 + 1, box_y0 + box_h, kBorderGold);
        fill_rect_rgba(out_px, w, h, box_x0 + box_w - 1, box_y0, box_x0 + box_w, box_y0 + box_h, kBorderGold);

        std::snprintf(line, sizeof(line), "%s | %s %s",
                      mode_name(st.mode), camera_mode_name(st.camera_mode),
                      st.paused ? "[PAUSED]" : "[PLAYING]");
        draw_text_rgba(out_px, w, h, box_x0 + 6, box_y0 + 5, line, kTextGold, 1);

        int y = box_y0 + 22;
        std::snprintf(line, sizeof(line), "FOV: %.0f DEG  SPD: %.0f  HUD: %s",
                      double(st.fov_deg), double(st.fly_speed), st.hide_hud ? "HIDDEN" : "SHOWN");
        draw_text_rgba(out_px, w, h, box_x0 + 6, y, line, kTextGreen, 1);
        y += 11;

        if (st.camera_mode == CameraMode::Orbit) {
            std::snprintf(line, sizeof(line), "TARGET: %s ([ / ] OR TAB CYCLE)",
                          st.orbit_target_label.empty() ? "PLAYER MECH" : st.orbit_target_label.c_str());
            draw_text_rgba(out_px, w, h, box_x0 + 6, y, line, kTextCyan, 1);
            y += 11;
        } else if (st.camera_mode == CameraMode::Dolly) {
            std::snprintf(line, sizeof(line), "DOLLY KEYFRAMES: %zu (K:ADD BKSP:DEL P:%s)",
                          st.dolly_keyframes, st.dolly_playing ? "STOP" : "PLAY");
            draw_text_rgba(out_px, w, h, box_x0 + 6, y, line, kTextCyan, 1);
            y += 11;
        }

        draw_text_rgba(out_px, w, h, box_x0 + 6, y, "F11: PHOTO / FREE CAM   F10: SAVE 60S REPLAY", kTextWhite, 1); y += 10;
        draw_text_rgba(out_px, w, h, box_x0 + 6, y, "C: CYCLE CAM            H: HIDE HUD/COCKPIT", kTextWhite, 1); y += 10;
        draw_text_rgba(out_px, w, h, box_x0 + 6, y, "WASD+QE: MOVE           MOUSE/ARROWS: LOOK", kTextWhite, 1); y += 10;
        draw_text_rgba(out_px, w, h, box_x0 + 6, y, "Z/X: ROLL (R:RST)       WHEEL/PGUP/DN: FOV", kTextWhite, 1); y += 10;
        draw_text_rgba(out_px, w, h, box_x0 + 6, y, "F9: SCREENSHOT          SHIFT+F9: 60FPS MP4", kTextGold, 1); y += 10;
        draw_text_rgba(out_px, w, h, box_x0 + 6, y, "F1: HIDE LEGEND         ESC: EXIT TO LIVE", kTextGreen, 1); y += 12;

        if (st.video_recording) {
            std::snprintf(line, sizeof(line), "REC 60FPS VIDEO [%u FRAMES]", st.video_frames_captured);
            draw_text_rgba(out_px, w, h, box_x0 + 6, y, line, kRecRed, 1);
        } else if (!st.status_banner.empty()) {
            draw_text_rgba(out_px, w, h, box_x0 + 6, y, st.status_banner, kTextGold, 1);
        }
    } else if (draw_status_only) {
        const std::string msg = st.video_recording
            ? ("REC 60FPS VIDEO [" + std::to_string(st.video_frames_captured) + " FRAMES]")
            : st.status_banner;
        const int pill_w = std::min<int>(int(w) - 2 * pad, int(msg.size()) * 6 + 14);
        fill_rect_rgba(out_px, w, h, box_x0, box_y0, box_x0 + pill_w, box_y0 + 18, kBgDark);
        fill_rect_rgba(out_px, w, h, box_x0, box_y0, box_x0 + pill_w, box_y0 + 1, kBorderGold);
        fill_rect_rgba(out_px, w, h, box_x0, box_y0 + 17, box_x0 + pill_w, box_y0 + 18, kBorderGold);
        draw_text_rgba(out_px, w, h, box_x0 + 6, box_y0 + 6, msg, st.video_recording ? kRecRed : kTextGold, 1);
    }

    // Bottom Replay Timeline Scrubber Bar when in Replay Mode
    if (st.mode == Mode::Replay && st.replay_total_frames > 0) {
        const int bar_h = 28;
        const int bar_y0 = int(h) - bar_h - pad;
        const int bar_x0 = pad;
        const int bar_w  = int(w) - 2 * pad;
        fill_rect_rgba(out_px, w, h, bar_x0, bar_y0, bar_x0 + bar_w, bar_y0 + bar_h, kBgDark);
        fill_rect_rgba(out_px, w, h, bar_x0, bar_y0, bar_x0 + bar_w, bar_y0 + 1, kBorderGold);
        fill_rect_rgba(out_px, w, h, bar_x0, bar_y0 + bar_h - 1, bar_x0 + bar_w, bar_y0 + bar_h, kBorderGold);

        const int track_x0 = bar_x0 + 8;
        const int track_w  = std::max(10, bar_w - 16);
        const int track_y0 = bar_y0 + 16;
        fill_rect_rgba(out_px, w, h, track_x0, track_y0, track_x0 + track_w, track_y0 + 6, 0xFF383838U);

        const float progress = (st.replay_total_frames > 1)
            ? std::clamp(float(st.replay_cur_frame) / float(st.replay_total_frames - 1), 0.0f, 1.0f)
            : 1.0f;
        const int fill_w = int(std::lround(progress * float(track_w)));
        fill_rect_rgba(out_px, w, h, track_x0, track_y0, track_x0 + fill_w, track_y0 + 6, kTextGreen);

        std::snprintf(line, sizeof(line), "REPLAY %05.1fS / %05.1fS  [FRAME %zu / %zu]  SPEED %.2fX  %s",
                      double(st.replay_cur_sec), double(st.replay_total_sec),
                      st.replay_cur_frame + 1, st.replay_total_frames,
                      double(st.playback_speed), st.paused ? "PAUSED" : "PLAYING");
        draw_text_rgba(out_px, w, h, track_x0, bar_y0 + 5, line, kTextGold, 1);
    }

    return true;
}

} // namespace mw34::photo_replay
