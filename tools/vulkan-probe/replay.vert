#version 450
layout(location=0) in vec4 position;
layout(location=1) in uint diffuse;
layout(location=2) in uint specular;
layout(location=3) in vec2 uv;
#ifdef AFFINE_UV
layout(location=0) noperspective out vec2 textureUV;
#else
layout(location=0) out vec2 textureUV;
#endif
#ifdef FLAT_SHADE
layout(location=1) flat out vec4 color;
#elif defined(PERSPECTIVE_COLOR)
layout(location=1) out vec4 color;
#else
layout(location=1) noperspective out vec4 color;
#endif
layout(location=2) noperspective out float fog;
layout(push_constant) uniform Push { vec4 viewport; vec4 fogColor; uint alphaModulate; uint fogEnabled; float offset; uint padding; } draw;
void main() {
    float w = 1.0 / position.w;
    vec2 screenPosition = position.xy;
#ifdef SNAP_GRID
    screenPosition = floor(screenPosition * float(SNAP_GRID) + 0.5) / float(SNAP_GRID);
#endif
    vec2 ndc = (screenPosition + draw.offset) / draw.viewport.zw * 2.0 - 1.0;
    gl_Position = vec4(ndc * w, position.z * w, w);
    textureUV = uv;
    color = vec4((diffuse >> 16) & 255, (diffuse >> 8) & 255, diffuse & 255, diffuse >> 24) / 255.0;
    fog = float(specular >> 24) / 255.0;
}
