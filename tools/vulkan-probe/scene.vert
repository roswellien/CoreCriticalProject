#version 450
layout(location=0) out vec2 uv;
layout(push_constant) uniform Draw { vec4 tint; vec4 options; } draw;
void main() {
    // Two triangles cover the target. Pixel-center UVs make nearest sampling
    // independently predictable without an authored game asset.
    const vec2 points[6] = vec2[6](vec2(-1,-1),vec2(1,-1),vec2(1,1),
                                  vec2(-1,-1),vec2(1,1),vec2(-1,1));
    vec2 p = points[gl_VertexIndex];
    uv = (p + 1.0) * 0.5;
    gl_Position = vec4(p, draw.options.x, 1.0);
}
