#version 450
// Direct3D 6 transformed-and-lit vertex (D3DFVF_TLVERTEX, 32 bytes): screen x,y, z, rhw, diffuse, specular, u,v.
layout(location=11) out vec4 radialEye;
layout(location=12) out vec3 radialScreen;
layout(location=0) in vec4 position;
layout(location=1) in uint diffuse;
layout(location=2) in uint specular;
layout(location=3) in vec2 uv;
layout(location=5) in vec4 rawFog;
layout(location=0) out vec2 uvPerspective;
layout(location=1) noperspective out vec2 uvAffine;
layout(location=2) out vec4 colorSmooth;
layout(location=3) flat out vec4 colorFlat;
layout(location=4) out vec4 specularSmooth;
layout(location=5) flat out vec4 specularFlat;
layout(location=10) out vec4 fogFactors;
layout(push_constant) uniform Push { vec4 target; vec4 fogColor; vec4 factor; uvec4 mode; vec4 radialProjection; } draw;
vec4 unpack(uint c) { return vec4((c >> 16) & 255u, (c >> 8) & 255u, c & 255u, c >> 24) / 255.0; }
void main() {
    fogFactors = rawFog;
    // Direct3D pixel centres lie on integer coordinates; Vulkan's lie on half-integers (target.z = 0.5).
    float w = 1.0 / position.w;
    vec2 ndc = (position.xy + draw.target.z) / draw.target.xy * 2.0 - 1.0;
    gl_Position = vec4(ndc * w, position.z * w, w);
    // TL may carry a texture RHW independent of reversed depth. Clip W
    // cancels perspective interpolation before the fragment divides by depth.
    vec2 offset = (position.xy - draw.radialProjection.zw) * draw.radialProjection.xy;
    radialScreen = gl_Position.xyw;
    radialEye = vec4(offset, draw.target.w, position.z) * w;
    gl_PointSize = 1.0;  // D3DPT_POINTLIST: one pixel (ignored for triangles)
    uvPerspective = uv;
    uvAffine = uv;
    colorSmooth = colorFlat = unpack(diffuse);
    specularSmooth = specularFlat = unpack(specular);
}
