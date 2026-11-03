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
void reject_alpha(float alpha) {
    uint flags=draw.mode.x;
    if ((flags & 32u) != 0u) {
        uint f = draw.mode.w & 255u;
        float r = float((draw.mode.w >> 8) & 255u) / 255.0;
        bool pass = f == 8u || (f == 2u && alpha < r) || (f == 3u && alpha == r) || (f == 4u && alpha <= r) ||
                    (f == 5u && alpha > r) || (f == 6u && alpha != r) || (f == 7u && alpha >= r);
        if (!pass) discard;
    }

}
