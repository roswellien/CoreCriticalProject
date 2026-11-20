// This file is included by the production material fragment shader. Height is
// linear UNORM red; the private numerical capture runs this exact trace.
bool pomFinite(vec2 value) {
    return !any(isnan(value)) && !any(isinf(value));
}
bool pomFinite(vec3 value) {
    return !any(isnan(value)) && !any(isinf(value));
}
float pomAddress(float value, uint policy) {
    if (policy == 1u) return fract(value);
    if (policy == 2u) return 1.0 - abs(mod(value, 2.0) - 1.0);
    return clamp(value, 0.0, 1.0);
}
float pomHeight(vec2 unwrapped, vec2 dx, vec2 dy) {
    vec2 extent = sun.pomAtlas.zw - sun.pomAtlas.xy;
    vec2 local = (unwrapped - sun.pomAtlas.xy) / extent;
    vec2 addressed = vec2(pomAddress(local.x, sun.pomPolicy.x),
                          pomAddress(local.y, sun.pomPolicy.y));
    // Height has one mip, linear filtering and no anisotropy. A half-texel
    // inset therefore bounds every tap, including at a mirrored/wrapped edge.
    vec2 inset = 0.5 / vec2(textureSize(heightMap, 0));
    vec2 sampleUV = clamp(sun.pomAtlas.xy + addressed * extent,
                          sun.pomAtlas.xy + inset, sun.pomAtlas.zw - inset);
    return textureGrad(heightMap, sampleUV, dx, dy).r;
}
vec2 pomTrace(vec2 baseUV, vec3 normal, vec3 dp1, vec3 dp2,
              vec2 duv1, vec2 duv2) {
    // Preserve the original bits, including negative zero, without chart
    // multiplication/division when relief is disabled or its amplitude is zero.
    float amplitude = sun.pomParams.z;
    if (sun.pomParams.x < 0.5 || amplitude == 0.0) return baseUV;
    if (!pomFinite(baseUV) || !pomFinite(normal) ||
        !pomFinite(dp1) || !pomFinite(dp2)) return baseUV;
    vec3 toEye = sun.surfaceEye.xyz - worldPosition;
    float eyeLength = length(toEye);
    if (!pomFinite(toEye) || !(eyeLength > 1e-12)) return baseUV;
    vec3 view = toEye / eyeLength;
    float incidence = dot(normal, view);
    if (!(incidence > 0.08)) return baseUV;
    // Unpack step bounds and world-unit distance LOD fade range from pomPolicy.zw.
    uint minSteps = clamp(sun.pomPolicy.z & 255u, 4u, 32u);
    uint maxSteps = clamp(sun.pomPolicy.w & 255u, minSteps, 32u);
    float fadeStart = float((sun.pomPolicy.z >> 8u) & 65535u);
    float fadeEnd = float((sun.pomPolicy.w >> 8u) & 65535u);
    // Scale effective distance by vertical zoom magnification (aspect-independent
    // on ultrawide viewports) so zoomed views keep surface relief crisp.
    float distanceFade = 1.0;
    if (fadeEnd > fadeStart && fadeEnd > 0.0) {
        float halfHeight = max(draw.target.y * 0.5, 1.0);
        float cotHalfFovY = abs(sun.projection.y * sun.extra.x) / halfHeight;
        float zoomScale = clamp(cotHalfFovY / 1.7320508, 1.0, 6.0);
        float effectiveDistance = eyeLength / zoomScale;
        if (effectiveDistance >= fadeEnd) return baseUV;
        distanceFade = 1.0 - smoothstep(fadeStart, fadeEnd, effectiveDistance);
    }
    // Taper relief smoothly near the grazing cutoff (0.08..0.14) to prevent a
    // hard seam on curved surfaces while preserving exact oracle hits at >=0.15.
    float grazingFade = smoothstep(0.08, 0.14, incidence);
    float effectiveAmplitude = amplitude * distanceFade * grazingFade;
    if (effectiveAmplitude == 0.0) return baseUV;
    float area = duv1.x * duv2.y - duv1.y * duv2.x;
    float footprint = dot(duv1, duv1) * dot(duv2, duv2);
    if (!(footprint > 0.0) || !(area * area > 1e-12 * footprint)) return baseUV;
    // Full inverse differential: do not normalize tangents, discard a mirrored
    // determinant, or use the normal-map perturbation as the surface metric.
    vec3 dpdu = (dp1 * duv2.y - dp2 * duv1.y) / area;
    vec3 dpdv = (dp2 * duv1.x - dp1 * duv2.x) / area;
    vec3 reciprocalU = cross(dpdv, normal);
    vec3 reciprocalV = cross(normal, dpdu);
    float determinant = dot(dpdu, reciprocalU);
    float metricScale = length(dpdu) * length(dpdv);
    if (!(metricScale > 0.0) || abs(determinant) <= 1e-6 * metricScale) return baseUV;
    vec3 ray = view / incidence;
    vec2 q = vec2(dot(reciprocalU, ray), dot(reciprocalV, ray)) / determinant;
    vec2 chart = baseUV * sun.pomUV.xy + sun.pomUV.zw;
    q *= sun.pomUV.xy;
    vec2 dx = duv1 * sun.pomUV.xy, dy = duv2 * sun.pomUV.xy;
    if (!pomFinite(q) || !pomFinite(chart) || !pomFinite(dx) || !pomFinite(dy)) return baseUV;
    float reference = sun.pomParams.y;
    float endpoint0 = effectiveAmplitude * -reference;
    float endpoint1 = effectiveAmplitude * (1.0 - reference);
    // Search from the eye towards the surface. Signed amplitudes change the
    // sorted interval, not the reference or the interpretation of the image.
    float high = max(endpoint0, endpoint1), low = min(endpoint0, endpoint1);
    int steps = int(mix(float(maxSteps), float(minSteps), incidence));
    steps = clamp(steps, int(minSteps), int(maxSteps));
    float upper = high;
    float upperF = upper - effectiveAmplitude * (pomHeight(chart + q * upper, dx, dy) - reference);
    float lower = low;
    bool found = upperF == 0.0;
    if (found) lower = upper;
    for (int stepIndex = 1; stepIndex <= 32 && !found; ++stepIndex) {
        if (stepIndex > steps) break;
        // The closed interval includes its low endpoint. Do not reconstruct
        // that final value through division/interpolation: a positive rounding
        // residual would miss an exact zero/one-height endpoint intersection.
        lower = stepIndex == steps ? low : mix(high, low, float(stepIndex) / float(steps));
        float lowerF = lower - effectiveAmplitude * (pomHeight(chart + q * lower, dx, dy) - reference);
        if (lowerF <= 0.0 || (stepIndex == steps && lowerF <= 1e-5 * abs(effectiveAmplitude))) found = true;
        else { upper = lower; upperF = lowerF; }
    }
    if (!found) return baseUV;
    int refineSteps = minSteps <= 4u ? 6 : 10;
    for (int refine = 0; refine < 10; ++refine) {
        if (refine >= refineSteps) break;
        float middle = 0.5 * (upper + lower);
        float value = middle - effectiveAmplitude * (pomHeight(chart + q * middle, dx, dy) - reference);
        if (value > 0.0) upper = middle;
        else lower = middle;
    }
    float t = 0.5 * (upper + lower);
    if (t == 0.0) return baseUV;
    // Invert the UNWRAPPED chart; inverting its addressed sample would move
    // albedo/normal into another base tile at repeat and mirror boundaries.
    // Algebraically inverse T(chart + q*t). Keep the original base term to
    // avoid cancelling a large chart offset before dividing by a small scale.
    vec2 displaced = baseUV + (q * t) / sun.pomUV.xy;
    return pomFinite(displaced) ? displaced : baseUV;
}
vec4 pomEncodeUV(vec2 uv) {
    // RG = U low/high byte; BA = V low/high byte, all four raw RGBA8 bytes.
    uvec2 packed = uvec2(round(clamp(uv, 0.0, 1.0) * 65535.0));
    return vec4(packed.x & 255u, packed.x >> 8u,
                packed.y & 255u, packed.y >> 8u) / 255.0;
}
