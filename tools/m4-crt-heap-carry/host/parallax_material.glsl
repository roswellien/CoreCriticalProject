// Parallax Occlusion Mapping (POM) fragment helper for MW34 Sun/Material shaders.
// Expects `sun` uniform block and `heightMap` (set = 2, binding = 1) sampler2D.

float pomApplyAddress1D(float x, uint mode) {
    if (mode == 2u) {
        float period = fract(x * 0.5) * 2.0;
        return period <= 1.0 ? period : 2.0 - period;
    }
    if (mode == 3u) {
        return clamp(x, 0.0, 1.0);
    }
    return fract(x);
}

vec2 pomResolveSampleUv(vec2 raw_uv, vec4 uv_transform, vec4 atlas_rect, uint addr_u, uint addr_v, vec2 inv_tex_size) {
    vec2 scaled = raw_uv * uv_transform.xy + uv_transform.zw;
    vec2 addressed = vec2(pomApplyAddress1D(scaled.x, addr_u), pomApplyAddress1D(scaled.y, addr_v));
    vec2 rect_min = atlas_rect.xy;
    vec2 rect_max = atlas_rect.zw;
    vec2 span = max(rect_max - rect_min, vec2(1e-6));
    vec2 mapped = rect_min + addressed * span;
    vec2 inset = min(0.5 * inv_tex_size, 0.25 * span);
    return clamp(mapped, rect_min + inset, rect_max - inset);
}

bool pomEvaluate(
    vec2 base_uv,
    vec3 world_pos,
    vec3 N,
    vec3 dp1,
    vec3 dp2,
    vec2 duv1,
    vec2 duv2,
    out vec2 out_uv,
    out vec2 out_ddx_uv,
    out vec2 out_ddy_uv,
    out vec3 out_debug_color
) {
    out_uv = base_uv;
    out_ddx_uv = duv1;
    out_ddy_uv = duv2;
    out_debug_color = vec3(0.0);

    bool debug_on = sun.pomFade.w > 0.5;
    if (sun.pomParams.x < 0.5 || sun.pomEye.w < 0.5) {
        return false;
    }

    vec3 eye_to_frag = sun.pomEye.xyz - world_pos;
    float dist = length(eye_to_frag);
    float fade_start = sun.pomFade.y;
    float fade_end = max(sun.pomFade.z, fade_start + 1e-3);
    float dist_fade = 1.0 - smoothstep(fade_start, fade_end, dist);

    vec3 dp2perp = cross(dp2, N);
    vec3 dp1perp = cross(N, dp1);
    vec3 T_raw = dp2perp * duv1.x + dp1perp * duv2.x;
    vec3 B_raw = dp2perp * duv1.y + dp1perp * duv2.y;
    float det = max(dot(T_raw, T_raw), dot(B_raw, B_raw));
    float uv_det = duv1.x * duv2.y - duv1.y * duv2.x;

    if (det <= 1e-20 || abs(uv_det) <= 1e-16) {
        if (debug_on) {
            out_debug_color = vec3(1.0, 0.2, 0.1);
            return true;
        }
        return false;
    }

    vec3 V = eye_to_frag / max(dist, 1e-6);
    float ndotv = dot(N, V);
    if (ndotv <= 0.08 || dist_fade <= 0.0) {
        if (debug_on) {
            out_debug_color = vec3(0.1, 0.35, 1.0);
            return true;
        }
        return false;
    }

    ivec2 tex_size_i = max(textureSize(heightMap, 0), ivec2(1));
    vec2 tex_size = vec2(tex_size_i);
    vec2 inv_tex_size = 1.0 / tex_size;
    vec2 ddx_scaled = duv1 * sun.pomUvTransform.xy;
    vec2 ddy_scaled = duv2 * sun.pomUvTransform.xy;
    out_ddx_uv = duv1;
    out_ddy_uv = duv2;

    float footprint = max(length(ddx_scaled * tex_size), length(ddy_scaled * tex_size));
    float mip_fade = 1.0 - smoothstep(1.5, 6.0, footprint);
    float grazing_fade = smoothstep(0.08, 0.25, ndotv);
    float effective_amp = sun.pomParams.z * dist_fade * mip_fade * grazing_fade;

    uint packed_addr = uint(sun.pomFade.x + 0.5);
    uint addr_u = packed_addr & 15u;
    uint addr_v = (packed_addr >> 4u) & 15u;

    if (abs(effective_amp) <= 1e-6) {
        out_uv = base_uv;
        if (debug_on) {
            out_debug_color = vec3(0.1, 0.85, 0.2);
            return true;
        }
        return false;
    }

    // Orthonormal tangent basis aligned with world units.
    // Cotangent identity: dp1 * duv2.y - dp2 * duv1.y = dP/du * uv_det.
    vec3 dPdu = (dp1 * duv2.y - dp2 * duv1.y) / uv_det;
    vec3 dPdv = (dp2 * duv1.x - dp1 * duv2.x) / uv_det;
    float du_world = max(length(dPdu), 1e-4);
    float dv_world = max(length(dPdv), 1e-4);
    float handedness = uv_det < 0.0 ? -1.0 : 1.0;

    vec3 T_unit = normalize(dPdu - N * dot(N, dPdu));
    vec3 B_ortho = cross(N, T_unit) * handedness;
    vec3 B_proj = dPdv - N * dot(N, dPdv);
    vec3 B_unit = dot(B_proj, B_proj) > 1e-12 ? normalize(B_proj) : B_ortho;
    if (dot(cross(T_unit, B_unit), N) * handedness < 0.0) {
        B_unit = -B_unit;
    }

    // View ray step in raw UV per unit world height.
    vec2 view_uv_per_world = vec2(dot(V, T_unit) / du_world, dot(V, B_unit) / dv_world);
    vec2 full_delta_uv = -view_uv_per_world * (effective_amp / max(ndotv, 0.08));
    float max_uv_span = 0.125;
    float delta_len = length(full_delta_uv);
    if (delta_len > max_uv_span) {
        full_delta_uv *= (max_uv_span / delta_len);
    }

    float max_steps = clamp(sun.pomParams.w, 8.0, 32.0);
    int num_steps = clamp(int(mix(max_steps, 8.0, clamp(ndotv, 0.0, 1.0)) + 0.5), 8, 32);
    float step_size = 1.0 / float(num_steps);

    float h_ref = clamp(sun.pomParams.y, 0.0, 1.0);
    float t_start = -h_ref;
    float t_end = 1.0 - h_ref;
    float t_span = t_end - t_start; // 1.0 normalized height range

    float prev_t = 0.0;
    vec2 prev_raw_uv = base_uv + full_delta_uv * (t_end - prev_t * t_span);
    vec2 prev_sample_uv = pomResolveSampleUv(prev_raw_uv, sun.pomUvTransform, sun.pomAtlasRect, addr_u, addr_v, inv_tex_size);
    float prev_ray_h = 1.0;
    float prev_tex_h = textureGrad(heightMap, prev_sample_uv, ddx_scaled, ddy_scaled).r;
    float prev_diff = prev_ray_h - prev_tex_h;

    float curr_t = 0.0;
    float curr_diff = prev_diff;
    int steps_taken = 0;

    if (prev_diff > 0.0) {
        for (int s = 1; s <= 32; ++s) {
            if (s > num_steps) {
                break;
            }
            steps_taken = s;
            curr_t = float(s) * step_size;
            vec2 raw_uv = base_uv + full_delta_uv * (t_end - curr_t * t_span);
            vec2 sample_uv = pomResolveSampleUv(raw_uv, sun.pomUvTransform, sun.pomAtlasRect, addr_u, addr_v, inv_tex_size);
            float ray_h = 1.0 - curr_t;
            float tex_h = textureGrad(heightMap, sample_uv, ddx_scaled, ddy_scaled).r;
            curr_diff = ray_h - tex_h;
            if (curr_diff <= 0.0) {
                break;
            }
            prev_t = curr_t;
            prev_diff = curr_diff;
        }
    }

    float best_t = curr_t;
    if (prev_diff > 0.0 && curr_diff <= 0.0) {
        float t0 = prev_t;
        float t1 = curr_t;
        float d0 = prev_diff;
        float d1 = curr_diff;
        for (int r = 0; r < 3; ++r) {
            float denom = d0 - d1;
            float tm = abs(denom) > 1e-6 ? clamp(t0 + d0 * (t1 - t0) / denom, t0, t1) : 0.5 * (t0 + t1);
            vec2 raw_uv = base_uv + full_delta_uv * (t_end - tm * t_span);
            vec2 sample_uv = pomResolveSampleUv(raw_uv, sun.pomUvTransform, sun.pomAtlasRect, addr_u, addr_v, inv_tex_size);
            float ray_h = 1.0 - tm;
            float tex_h = textureGrad(heightMap, sample_uv, ddx_scaled, ddy_scaled).r;
            float dm = ray_h - tex_h;
            if (dm > 0.0) {
                t0 = tm;
                d0 = dm;
            } else {
                t1 = tm;
                d1 = dm;
            }
            best_t = tm;
        }
    }

    vec2 final_raw_uv = base_uv + full_delta_uv * (t_end - best_t * t_span);
    // Base and normal textures use raw draw UVs; only heightMap uses the resolved UV.
    out_uv = final_raw_uv;
    if (debug_on) {
        float step_ratio = float(steps_taken) / float(max(num_steps, 1));
        out_debug_color = vec3(0.15 + 0.85 * step_ratio, 0.85 * dist_fade * mip_fade, clamp(1.0 - best_t, 0.0, 1.0));
    }
    return true;
}
