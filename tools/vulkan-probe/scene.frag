#version 450
layout(location=0) in vec2 uv;
layout(location=0) out vec4 color;
layout(set=0,binding=0) uniform sampler2D authoredTexture;
layout(push_constant) uniform Draw { vec4 tint; vec4 options; } draw;
void main() {
    vec4 base = texture(authoredTexture, uv) * draw.tint;
    color = vec4(mix(base.rgb, vec3(0.25), draw.options.y), base.a);
}
