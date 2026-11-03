#version 450
// Output-resolution coverage replay for opaque reduced world submissions.
// Preserve original texture alpha testing; expensive RGB shading is already in the input.
layout(location=0) in vec2 uvPerspective;
layout(location=1) noperspective in vec2 uvAffine;
layout(location=2) noperspective in vec4 colorSmooth;
layout(location=3) flat in vec4 colorFlat;
layout(location=4) noperspective in vec4 specularSmooth;
layout(location=5) flat in vec4 specularFlat;
layout(set=0,binding=0) uniform sampler2D image;
layout(set=0,binding=1) uniform sampler2D reconstructedWorld;
layout(location=0) out vec4 result;
// mode.x flags: 1 flat, 2 perspective, 4 textured, 8 specular, 16 fog, 32 alpha test.
// mode.y colour op | arg1 << 8 | arg2 << 16; mode.z alpha op | arg1 << 8 | arg2 << 16;
// mode.w alpha function | reference << 8.
layout(push_constant) uniform Push { vec4 target; vec4 fogColor; vec4 factor; uvec4 mode; } draw;
#extension GL_GOOGLE_include_directive : require
#include "fragment_alpha.glsl"
void main() {
    uint flags = draw.mode.x;
    diffuse = (flags & 1u) != 0u ? colorFlat : colorSmooth;
    specular = (flags & 1u) != 0u ? specularFlat : specularSmooth;
    vec2 uv = (flags & 2u) != 0u ? uvPerspective : uvAffine;
    texel = (flags & 4u) != 0u ? texture(image, uv) : vec4(1.0);
    float alpha = operation(draw.mode.z).a;
    reject_alpha(alpha);
    result = textureLod(reconstructedWorld, gl_FragCoord.xy / vec2(textureSize(reconstructedWorld, 0)), 0.0);
    // Later full-resolution passes can use destination-alpha blend factors.
    // Only RGB comes from reconstruction; alpha follows the original fragment.
    result.a = alpha;
}
