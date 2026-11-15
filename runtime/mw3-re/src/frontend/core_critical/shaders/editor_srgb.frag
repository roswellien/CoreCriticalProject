// Editor-only fragment variant for a selected sRGB output attachment.
// Match the vendor vertex interface and separate image/sampler sets exactly.
#version 450 core
layout(location = 0) out vec4 fColor;
layout(set = 0, binding = 0) uniform texture2D _Texture;
layout(set = 1, binding = 0) uniform sampler _Sampler;
layout(location = 0) in struct { vec4 Color; vec2 UV; } In;
vec3 srgb_to_linear(vec3 value)
{
    vec3 low = value / 12.92;
    vec3 high = pow((value + vec3(0.055)) / 1.055, vec3(2.4));
    return mix(high, low, lessThanEqual(value, vec3(0.04045)));
}
void main()
{
    vec4 combined = In.Color * texture(sampler2D(_Texture, _Sampler), In.UV.st);
    fColor = vec4(srgb_to_linear(combined.rgb), combined.a);
}
