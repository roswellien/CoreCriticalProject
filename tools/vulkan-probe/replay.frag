#version 450
#ifdef AFFINE_UV
layout(location=0) noperspective in vec2 textureUV;
#else
layout(location=0) in vec2 textureUV;
#endif
#ifdef FLAT_SHADE
layout(location=1) flat in vec4 color;
#elif defined(PERSPECTIVE_COLOR)
layout(location=1) in vec4 color;
#else
layout(location=1) noperspective in vec4 color;
#endif
layout(location=2) noperspective in float fog;
layout(set=0,binding=0) uniform sampler2D image;
layout(location=0) out vec4 result;
layout(push_constant) uniform Push { vec4 viewport; vec4 fogColor; uint alphaModulate; uint fogEnabled; float offset; uint padding; } draw;
void main() {
    vec4 texel = texture(image,textureUV);
    vec3 rgb = texel.rgb * color.rgb;
    if (draw.fogEnabled != 0) rgb = mix(draw.fogColor.rgb,rgb,clamp(fog,0.0,1.0));
#ifdef QUANTIZE_565
    vec3 levels = vec3(31.0,63.0,31.0);
#ifdef DITHER_4X4
    const int bayer[16] = int[16](0,8,2,10,12,4,14,6,3,11,1,9,15,7,13,5);
    ivec2 pixel = ivec2(gl_FragCoord.xy) & ivec2(3);
    float threshold = (float(bayer[pixel.y*4+pixel.x]) + 0.5)/16.0 - 0.5;
    rgb += vec3(threshold)/levels;
#endif
    rgb = floor(clamp(rgb,0.0,1.0)*levels+0.5)/levels;
#endif
    result = vec4(rgb,texel.a * (draw.alphaModulate != 0 ? color.a : 1.0));
}
