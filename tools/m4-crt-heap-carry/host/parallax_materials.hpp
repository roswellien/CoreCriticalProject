#pragma once
#include "surface_materials.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace mw34::materials {

struct PomVec2 {
    float x{}, y{};
};

struct PomVec3 {
    float x{}, y{}, z{};
};

struct PomUniformInput {
    std::array<float, 4> pom_params{};       // (active, height_reference, height_amplitude, max_steps)
    std::array<float, 4> pom_uv_transform{}; // (uv_scale.x, uv_scale.y, uv_offset.x, uv_offset.y)
    std::array<float, 4> pom_atlas_rect{};   // (min_u, min_v, max_u, max_v)
    std::array<float, 4> pom_fade{};         // (packed_address_u_v, fade_start_dist, fade_end_dist, debug_mode)
    std::array<float, 4> pom_eye{};          // (eye_x, eye_y, eye_z, eye_valid)
};

struct PomEvalResult {
    bool applied{};
    PomVec2 uv{};
    PomVec2 ddx_uv{};
    PomVec2 ddy_uv{};
    PomVec3 debug_color{};
    int steps_taken{};
    float best_t{};
};

inline float pom_dot(PomVec2 a, PomVec2 b) { return a.x * b.x + a.y * b.y; }
inline float pom_dot(PomVec3 a, PomVec3 b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline float pom_length(PomVec2 v) { return std::sqrt(pom_dot(v, v)); }
inline float pom_length(PomVec3 v) { return std::sqrt(pom_dot(v, v)); }

inline PomVec3 pom_cross(PomVec3 a, PomVec3 b) {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    };
}

inline PomVec3 pom_normalize(PomVec3 v) {
    const float len = pom_length(v);
    if (len <= 1e-20f)
        return {0.0f, 0.0f, 0.0f};
    return {v.x / len, v.y / len, v.z / len};
}

inline float pom_fract(float x) { return x - std::floor(x); }

inline float pom_smoothstep(float edge0, float edge1, float x) {
    const float span = std::max(edge1 - edge0, 1e-6f);
    const float t = std::clamp((x - edge0) / span, 0.0f, 1.0f);
    return t * t * (3.0f - 2.0f * t);
}

inline float pom_apply_address_1d(float x, std::uint32_t mode) {
    if (mode == surface_address_mirror) {
        const float period = pom_fract(x * 0.5f) * 2.0f;
        return period <= 1.0f ? period : 2.0f - period;
    }
    if (mode == surface_address_clamp)
        return std::clamp(x, 0.0f, 1.0f);
    return pom_fract(x);
}

inline PomVec2 pom_resolve_sample_uv(PomVec2 raw_uv, const std::array<float, 4> &uv_transform,
                                     const std::array<float, 4> &atlas_rect, std::uint32_t addr_u,
                                     std::uint32_t addr_v, PomVec2 inv_tex_size) {
    const PomVec2 scaled{
        raw_uv.x * uv_transform[0] + uv_transform[2],
        raw_uv.y * uv_transform[1] + uv_transform[3],
    };
    const PomVec2 addressed{
        pom_apply_address_1d(scaled.x, addr_u),
        pom_apply_address_1d(scaled.y, addr_v),
    };
    const PomVec2 rect_min{atlas_rect[0], atlas_rect[1]};
    const PomVec2 rect_max{atlas_rect[2], atlas_rect[3]};
    const PomVec2 span{
        std::max(rect_max.x - rect_min.x, 1e-6f),
        std::max(rect_max.y - rect_min.y, 1e-6f),
    };
    const PomVec2 mapped{
        rect_min.x + addressed.x * span.x,
        rect_min.y + addressed.y * span.y,
    };
    const PomVec2 inset{
        std::min(0.5f * inv_tex_size.x, 0.25f * span.x),
        std::min(0.5f * inv_tex_size.y, 0.25f * span.y),
    };
    return {
        std::clamp(mapped.x, rect_min.x + inset.x, rect_max.x - inset.x),
        std::clamp(mapped.y, rect_min.y + inset.y, rect_max.y - inset.y),
    };
}

// Bilinear red-channel height sampler over a SurfaceMaterialImage.
inline float sample_height_bilinear(const SurfaceMaterialImage &img, PomVec2 uv) {
    if (!img.width || !img.height || img.pixels.empty())
        return 0.0f;
    const float w = static_cast<float>(img.width);
    const float h = static_cast<float>(img.height);
    const float px = std::clamp(uv.x, 0.0f, 1.0f) * w - 0.5f;
    const float py = std::clamp(uv.y, 0.0f, 1.0f) * h - 0.5f;
    const int x0 = std::clamp(static_cast<int>(std::floor(px)), 0, static_cast<int>(img.width) - 1);
    const int y0 = std::clamp(static_cast<int>(std::floor(py)), 0, static_cast<int>(img.height) - 1);
    const int x1 = std::clamp(x0 + 1, 0, static_cast<int>(img.width) - 1);
    const int y1 = std::clamp(y0 + 1, 0, static_cast<int>(img.height) - 1);
    const float fx = std::clamp(px - std::floor(px), 0.0f, 1.0f);
    const float fy = std::clamp(py - std::floor(py), 0.0f, 1.0f);

    auto red_at = [&](int x, int y) {
        const auto idx =
            static_cast<std::size_t>(y) * static_cast<std::size_t>(img.width) + static_cast<std::size_t>(x);
        return static_cast<float>(img.pixels[idx] & 0xffU) / 255.0f;
    };
    const float h00 = red_at(x0, y0);
    const float h10 = red_at(x1, y0);
    const float h01 = red_at(x0, y1);
    const float h11 = red_at(x1, y1);
    const float hx0 = h00 + (h10 - h00) * fx;
    const float hx1 = h01 + (h11 - h01) * fx;
    return hx0 + (hx1 - hx0) * fy;
}

template <typename HeightSampler>
inline PomEvalResult evaluate_pom(PomVec2 base_uv, PomVec3 world_pos, PomVec3 N, PomVec3 dp1,
                                  PomVec3 dp2, PomVec2 duv1, PomVec2 duv2,
                                  const PomUniformInput &sun, std::uint32_t tex_width,
                                  std::uint32_t tex_height, HeightSampler &&sample_height) {
    PomEvalResult res{};
    res.uv = base_uv;
    res.ddx_uv = duv1;
    res.ddy_uv = duv2;

    const bool debug_on = sun.pom_fade[3] > 0.5f;
    if (sun.pom_params[0] < 0.5f || sun.pom_eye[3] < 0.5f)
        return res;

    const PomVec3 eye_to_frag{
        sun.pom_eye[0] - world_pos.x,
        sun.pom_eye[1] - world_pos.y,
        sun.pom_eye[2] - world_pos.z,
    };
    const float dist = pom_length(eye_to_frag);
    const float fade_start = sun.pom_fade[1];
    const float fade_end = std::max(sun.pom_fade[2], fade_start + 1e-3f);
    const float dist_fade = 1.0f - pom_smoothstep(fade_start, fade_end, dist);

    const PomVec3 dp2perp = pom_cross(dp2, N);
    const PomVec3 dp1perp = pom_cross(N, dp1);
    const PomVec3 T_raw{
        dp2perp.x * duv1.x + dp1perp.x * duv2.x,
        dp2perp.y * duv1.x + dp1perp.y * duv2.x,
        dp2perp.z * duv1.x + dp1perp.z * duv2.x,
    };
    const PomVec3 B_raw{
        dp2perp.x * duv1.y + dp1perp.x * duv2.y,
        dp2perp.y * duv1.y + dp1perp.y * duv2.y,
        dp2perp.z * duv1.y + dp1perp.z * duv2.y,
    };
    const float det = std::max(pom_dot(T_raw, T_raw), pom_dot(B_raw, B_raw));
    const float uv_det = duv1.x * duv2.y - duv1.y * duv2.x;

    if (det <= 1e-20f || std::abs(uv_det) <= 1e-16f) {
        if (debug_on) {
            res.applied = true;
            res.debug_color = {1.0f, 0.2f, 0.1f};
        }
        return res;
    }

    const float inv_dist = 1.0f / std::max(dist, 1e-6f);
    const PomVec3 V{eye_to_frag.x * inv_dist, eye_to_frag.y * inv_dist, eye_to_frag.z * inv_dist};
    const float ndotv = pom_dot(N, V);
    if (ndotv <= 0.08f || dist_fade <= 0.0f) {
        if (debug_on) {
            res.applied = true;
            res.debug_color = {0.1f, 0.35f, 1.0f};
        }
        return res;
    }

    const float tw = static_cast<float>(std::max(tex_width, 1U));
    const float th = static_cast<float>(std::max(tex_height, 1U));
    const PomVec2 inv_tex_size{1.0f / tw, 1.0f / th};
    const PomVec2 atlas_span{sun.pom_atlas_rect[2] - sun.pom_atlas_rect[0],
                             sun.pom_atlas_rect[3] - sun.pom_atlas_rect[1]};
    const PomVec2 ddx_scaled{duv1.x * sun.pom_uv_transform[0] * atlas_span.x,
                             duv1.y * sun.pom_uv_transform[1] * atlas_span.y};
    const PomVec2 ddy_scaled{duv2.x * sun.pom_uv_transform[0] * atlas_span.x,
                             duv2.y * sun.pom_uv_transform[1] * atlas_span.y};

    const float footprint = std::max(pom_length(PomVec2{ddx_scaled.x * tw, ddx_scaled.y * th}),
                                     pom_length(PomVec2{ddy_scaled.x * tw, ddy_scaled.y * th}));
    const float mip_fade = 1.0f - pom_smoothstep(1.5f, 6.0f, footprint);
    const float grazing_fade = pom_smoothstep(0.08f, 0.25f, ndotv);
    const float effective_amp = sun.pom_params[2] * dist_fade * mip_fade * grazing_fade;

    const auto packed_addr = static_cast<std::uint32_t>(sun.pom_fade[0] + 0.5f);
    const std::uint32_t addr_u = packed_addr & 15U;
    const std::uint32_t addr_v = (packed_addr >> 4U) & 15U;

    if (std::abs(effective_amp) <= 1e-6f) {
        if (debug_on) {
            res.applied = true;
            res.debug_color = {0.1f, 0.85f, 0.2f};
        }
        return res;
    }

    const PomVec3 dPdu{
        (dp1.x * duv2.y - dp2.x * duv1.y) / uv_det,
        (dp1.y * duv2.y - dp2.y * duv1.y) / uv_det,
        (dp1.z * duv2.y - dp2.z * duv1.y) / uv_det,
    };
    const PomVec3 dPdv{
        (dp2.x * duv1.x - dp1.x * duv2.x) / uv_det,
        (dp2.y * duv1.x - dp1.y * duv2.x) / uv_det,
        (dp2.z * duv1.x - dp1.z * duv2.x) / uv_det,
    };
    const float ndotpdu = pom_dot(N, dPdu);
    const float ndotpdv = pom_dot(N, dPdv);
    const PomVec3 tangent_u{dPdu.x - N.x * ndotpdu, dPdu.y - N.y * ndotpdu,
                            dPdu.z - N.z * ndotpdu};
    const PomVec3 tangent_v{dPdv.x - N.x * ndotpdv, dPdv.y - N.y * ndotpdv,
                            dPdv.z - N.z * ndotpdv};
    const float metric_uu = pom_dot(tangent_u, tangent_u);
    const float metric_uv = pom_dot(tangent_u, tangent_v);
    const float metric_vv = pom_dot(tangent_v, tangent_v);
    const float metric_det = metric_uu * metric_vv - metric_uv * metric_uv;
    if (metric_det <= 1e-12f * metric_uu * metric_vv) {
        if (debug_on) {
            res.applied = true;
            res.debug_color = {1.0f, 0.2f, 0.1f};
        }
        return res;
    }

    // Solve the reciprocal tangent basis, not independent projections (which shear skewed UVs).
    const float view_u = pom_dot(V, tangent_u);
    const float view_v = pom_dot(V, tangent_v);
    const PomVec2 view_uv_per_world{(view_u * metric_vv - view_v * metric_uv) / metric_det,
                                    (view_v * metric_uu - view_u * metric_uv) / metric_det};
    const float scale_factor = -effective_amp / std::max(ndotv, 0.08f);
    PomVec2 full_delta_uv{view_uv_per_world.x * scale_factor, view_uv_per_world.y * scale_factor};
    constexpr float max_uv_span = 0.125f;
    const float delta_len = pom_length(full_delta_uv);
    if (delta_len > max_uv_span) {
        full_delta_uv.x *= max_uv_span / delta_len;
        full_delta_uv.y *= max_uv_span / delta_len;
    }

    const float max_steps = std::clamp(sun.pom_params[3], 8.0f, 32.0f);
    const float interp_steps =
        max_steps + (8.0f - max_steps) * std::clamp(ndotv, 0.0f, 1.0f) + 0.5f;
    const int num_steps = std::clamp(static_cast<int>(interp_steps), 8, 32);
    const float step_size = 1.0f / static_cast<float>(num_steps);

    const float h_ref = std::clamp(sun.pom_params[1], 0.0f, 1.0f);
    const float t_start = -h_ref;
    const float t_end = 1.0f - h_ref;
    const float t_span = t_end - t_start;

    float prev_t = 0.0f;
    const PomVec2 prev_raw_uv{
        base_uv.x + full_delta_uv.x * (t_end - prev_t * t_span),
        base_uv.y + full_delta_uv.y * (t_end - prev_t * t_span),
    };
    const PomVec2 prev_sample_uv = pom_resolve_sample_uv(
        prev_raw_uv, sun.pom_uv_transform, sun.pom_atlas_rect, addr_u, addr_v, inv_tex_size);
    const float prev_tex_h = sample_height(prev_sample_uv);
    float prev_diff = 1.0f - prev_tex_h;

    float curr_t = 0.0f;
    float curr_diff = prev_diff;
    int steps_taken = 0;

    if (prev_diff > 0.0f) {
        for (int s = 1; s <= 32; ++s) {
            if (s > num_steps)
                break;
            steps_taken = s;
            curr_t = static_cast<float>(s) * step_size;
            const PomVec2 raw_uv{
                base_uv.x + full_delta_uv.x * (t_end - curr_t * t_span),
                base_uv.y + full_delta_uv.y * (t_end - curr_t * t_span),
            };
            const PomVec2 sample_uv = pom_resolve_sample_uv(
                raw_uv, sun.pom_uv_transform, sun.pom_atlas_rect, addr_u, addr_v, inv_tex_size);
            const float ray_h = 1.0f - curr_t;
            const float tex_h = sample_height(sample_uv);
            curr_diff = ray_h - tex_h;
            if (curr_diff <= 0.0f)
                break;
            prev_t = curr_t;
            prev_diff = curr_diff;
        }
    }

    float best_t = curr_t;
    if (prev_diff > 0.0f && curr_diff <= 0.0f) {
        float t0 = prev_t;
        float t1 = curr_t;
        float d0 = prev_diff;
        float d1 = curr_diff;
        for (int r = 0; r < 3; ++r) {
            const float denom = d0 - d1;
            const float tm = std::abs(denom) > 1e-6f
                                 ? std::clamp(t0 + d0 * (t1 - t0) / denom, t0, t1)
                                 : 0.5f * (t0 + t1);
            const PomVec2 raw_uv{
                base_uv.x + full_delta_uv.x * (t_end - tm * t_span),
                base_uv.y + full_delta_uv.y * (t_end - tm * t_span),
            };
            const PomVec2 sample_uv = pom_resolve_sample_uv(
                raw_uv, sun.pom_uv_transform, sun.pom_atlas_rect, addr_u, addr_v, inv_tex_size);
            const float ray_h = 1.0f - tm;
            const float tex_h = sample_height(sample_uv);
            const float dm = ray_h - tex_h;
            if (dm > 0.0f) {
                t0 = tm;
                d0 = dm;
            } else {
                t1 = tm;
                d1 = dm;
            }
            best_t = tm;
        }
    }

    const PomVec2 final_raw_uv{
        base_uv.x + full_delta_uv.x * (t_end - best_t * t_span),
        base_uv.y + full_delta_uv.y * (t_end - best_t * t_span),
    };
    res.applied = true;
    res.steps_taken = steps_taken;
    res.best_t = best_t;
    res.uv = final_raw_uv;
    if (debug_on) {
        const float step_ratio =
            static_cast<float>(steps_taken) / static_cast<float>(std::max(num_steps, 1));
        res.debug_color = {
            0.15f + 0.85f * step_ratio,
            0.85f * dist_fade * mip_fade,
            std::clamp(1.0f - best_t, 0.0f, 1.0f),
        };
    }
    return res;
}

} // namespace mw34::materials
