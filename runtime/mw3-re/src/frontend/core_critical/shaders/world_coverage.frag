#version 450
#extension GL_GOOGLE_include_directive : require
// Output-resolution coverage replay for opaque reduced world submissions.
// Preserve original texture alpha testing; expensive RGB shading is already in the input.
#include "radial_visibility.glsl"
layout(location=11) in vec4 radialEye;
layout(location=0) in vec2 uvPerspective;
layout(location=1) noperspective in vec2 uvAffine;
layout(location=2) noperspective in vec4 colorSmooth;
layout(location=3) flat in vec4 colorFlat;
layout(location=4) noperspective in vec4 specularSmooth;
layout(location=5) flat in vec4 specularFlat;
layout(location=10) in vec4 fogFactors;
layout(set=0,binding=0) uniform sampler2D image;
layout(set=0,binding=1) uniform sampler2D reconstructedWorld;
layout(location=0) out vec4 result;
// mode.x flags: 1 flat, 2 perspective, 4 textured, 8 specular, 16 fog, 32 alpha test.
// mode.y colour op | arg1 << 8 | arg2 << 16; mode.z alpha op | arg1 << 8 | arg2 << 16;
// mode.w alpha function | reference << 8.
layout(push_constant) uniform Push { vec4 target; vec4 fogColor; vec4 factor; uvec4 mode; } draw;
vec4 diffuse, specular, texel;
vec4 argument(uint a) {
    vec4 v;
    uint s = a & 15u;
    if (s == 0u || s == 1u) v = diffuse;      // D3DTA_DIFFUSE, D3DTA_CURRENT (stage 0: diffuse)
    else if (s == 2u) v = texel;              // D3DTA_TEXTURE
    else if (s == 3u) v = draw.factor;        // D3DTA_TFACTOR
    else v = specular;                        // D3DTA_SPECULAR
    if ((a & 16u) != 0u) v = 1.0 - v;         // D3DTA_COMPLEMENT
    if ((a & 32u) != 0u) v = vec4(v.a);       // D3DTA_ALPHAREPLICATE
    return v;
}
vec4 operation(uint word) {
    uint op = word & 255u;
    vec4 a = argument((word >> 8) & 255u), b = argument((word >> 16) & 255u);
    if (op == 1u) return diffuse;                         // DISABLE: current passes through
    if (op == 2u) return a;                               // SELECTARG1
    if (op == 3u) return b;                               // SELECTARG2
    if (op == 4u) return a * b;                           // MODULATE
    if (op == 5u) return min(a * b * 2.0, 1.0);           // MODULATE2X
    if (op == 6u) return min(a * b * 4.0, 1.0);           // MODULATE4X
    if (op == 7u) return min(a + b, 1.0);                 // ADD
    if (op == 8u) return clamp(a + b - 0.5, 0.0, 1.0);    // ADDSIGNED
    if (op == 9u) return clamp((a + b - 0.5) * 2.0, 0.0, 1.0); // ADDSIGNED2X
    if (op == 10u) return clamp(a - b, 0.0, 1.0);         // SUBTRACT
    if (op == 11u) return min(a + b - a * b, 1.0);        // ADDSMOOTH
    if (op == 12u) return mix(b, a, diffuse.a);           // BLENDDIFFUSEALPHA
    if (op == 13u) return mix(b, a, texel.a);             // BLENDTEXTUREALPHA
    return mix(b, a, draw.factor.a);                      // BLENDFACTORALPHA (14)
}
void shadeScene() {
    uint flags = draw.mode.x;
    diffuse = (flags & 1u) != 0u ? colorFlat : colorSmooth;
    specular = (flags & 1u) != 0u ? specularFlat : specularSmooth;
    if (fogFactors.w > 0.5) {
        vec3 amounts = clamp(fogFactors.xyz, 0.0, 1.0);
        specular.a = (1.0 - amounts.x * amounts.y) * (1.0 - amounts.z);
    }
    vec2 uv = (flags & 2u) != 0u ? uvPerspective : uvAffine;
    texel = (flags & 4u) != 0u ? texture(image, uv) : vec4(1.0);
    // Tinted world draws store their blend weight in mode.z, but renderer setup
    // pins world scale to 100%, so they never enter this coverage replay pass.
    float alpha = operation(draw.mode.z).a;
    if ((flags & 32u) != 0u) {
        uint f = draw.mode.w & 255u;
        float r = float((draw.mode.w >> 8) & 255u) / 255.0;
        bool pass = f == 8u || (f == 2u && alpha < r) || (f == 3u && alpha == r) || (f == 4u && alpha <= r) ||
                    (f == 5u && alpha > r) || (f == 6u && alpha != r) || (f == 7u && alpha >= r);
        if (!pass) discard;
    }
    result = textureLod(reconstructedWorld, gl_FragCoord.xy / vec2(textureSize(reconstructedWorld, 0)), 0.0);
    // Later full-resolution passes can use destination-alpha blend factors.
    // Only RGB comes from reconstruction; alpha follows the original fragment.
    result.a = alpha;
}

void main() {
    vec4 visibility = radialVisibility(radialEye, ivec2(gl_FragCoord.xy), draw.mode.x);
    shadeScene();
    result.rgb = mix(visibility.rgb, result.rgb, visibility.a);
}
