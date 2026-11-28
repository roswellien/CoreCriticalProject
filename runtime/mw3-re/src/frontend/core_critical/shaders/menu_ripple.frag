#version 450
layout(location = 0) in vec2 uv;
layout(set = 0, binding = 0) uniform sampler2D sourceColor;
layout(location = 0) out vec4 outColor;
layout(push_constant, std430) uniform Push {
    vec4 center_scale;
    vec4 wave_params;
    vec4 phase_invsize;
    vec4 clip_uv;
} ripple;
void main() {
    if (ripple.phase_invsize.y > 0.5 &&
        (uv.x < ripple.clip_uv.x || uv.y < ripple.clip_uv.y ||
         uv.x >= ripple.clip_uv.z || uv.y >= ripple.clip_uv.w)) discard;
    vec2 deltaLogical = (uv - ripple.center_scale.xy) / ripple.center_scale.zw;
    float r = length(deltaLogical);
    float inner = ripple.wave_params.x;
    float outer = ripple.wave_params.y;
    if (r <= inner || r >= outer || r <= 1e-4) discard;
    float t = clamp((r - inner) / max(outer - inner, 1e-4), 0.0, 1.0);
    // Reverse the increasing smoothstep explicitly: reversed edges are undefined in GLSL.
    float edgeEnvelope = smoothstep(0.0, 0.25, t) * (1.0 - smoothstep(0.75, 1.0, t));
    float centerGuard = inner <= 0.0 ? smoothstep(0.0, min(outer * 0.25, 6.0), r) : 1.0;
    float wave = sin(r / max(ripple.wave_params.w, 1e-4) + ripple.phase_invsize.x)
               * ripple.wave_params.z * edgeEnvelope * centerGuard;
    vec2 displacedLogical = deltaLogical + (deltaLogical / r) * wave;
    vec2 srcUv = ripple.center_scale.xy + displacedLogical * ripple.center_scale.zw;
    vec2 minUv = ripple.phase_invsize.zw;
    vec2 maxUv = vec2(1.0) - ripple.phase_invsize.zw;
    if (ripple.phase_invsize.y > 0.5) {
        minUv = max(minUv, ripple.clip_uv.xy + ripple.phase_invsize.zw);
        maxUv = min(maxUv, ripple.clip_uv.zw - ripple.phase_invsize.zw);
        if (maxUv.x < minUv.x) minUv.x = maxUv.x = 0.5 * (ripple.clip_uv.x + ripple.clip_uv.z);
        if (maxUv.y < minUv.y) minUv.y = maxUv.y = 0.5 * (ripple.clip_uv.y + ripple.clip_uv.w);
    }
    outColor = texture(sourceColor, clamp(srcUv, minUv, maxUv));
}
