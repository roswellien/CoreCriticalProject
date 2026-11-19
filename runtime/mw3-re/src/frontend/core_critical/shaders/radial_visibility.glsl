// A spatial coverage fallback serves blended draws and views without a known
// backdrop. All output passes use the same sample rank.
int radialBayerPair(ivec2 p) {
    return (((p.x ^ p.y) & 1) << 1) | (p.y & 1);
}

layout(set=0,binding=2) uniform sampler2D radialBackdrop;
layout(location=12) in vec3 radialScreen;

vec4 radialVisibility(vec4 eye, ivec2 pixel, uint flags) {
    // eye.xyz / eye.w is the perspective-correct camera vector in units of
    // the selected range. A zero denominator disables this draw's range.
    if (eye.w <= 0.0) return vec4(0,0,0,1);
    float distanceSquared = dot(eye.xyz, eye.xyz);
    float farSquared = eye.w * eye.w;
    if (distanceSquared <= 0.64 * farSquared) return vec4(0,0,0,1);
    if (distanceSquared >= farSquared) discard;
    float coverage = 1.0 - smoothstep(0.8, 1.0, sqrt(distanceSquared) / eye.w);
    // mode.x bits 15/14 select the authored sky or copied zoom scissor.
    if ((flags & (1u << 15)) != 0u) {
        vec2 uv = radialScreen.xy / radialScreen.z * 0.5 + 0.5;
        if ((flags & (1u << 14)) != 0u) {
            // texelFetch does not clamp: a fragment at or past the screen edge would read outside.
            ivec2 size = textureSize(radialBackdrop, 0);
            ivec2 at = clamp(ivec2(uv * vec2(size)), ivec2(0), size - ivec2(1));
            return vec4(texelFetch(radialBackdrop, at, 0).rgb, coverage);
        }
        vec4 sky = textureLod(radialBackdrop, uv, 0.0);
        if (sky.a == 1.0) return vec4(sky.rgb, coverage);
    }
    int rank = (radialBayerPair(pixel) << 4) | (radialBayerPair(pixel >> 1) << 2)
               | radialBayerPair(pixel >> 2);
    if (coverage <= (float(rank) + 0.5) / 64.0) discard;
    return vec4(0,0,0,1);
}
