#version 450
layout(location=11) out vec4 radialEye;
layout(location=12) out vec3 radialScreen;
layout(location=0) in vec3 position;
layout(location=1) in vec3 normal;
layout(location=2) in vec2 uv;
layout(location=0) out vec2 uvPerspective;
layout(location=1) noperspective out vec2 uvAffine;
layout(location=2) out vec4 colorSmooth;
layout(location=3) flat out vec4 colorFlat;
layout(location=4) out vec4 specularSmooth;
layout(location=5) flat out vec4 specularFlat;
layout(location=6) out vec3 worldNormal;
layout(location=7) out vec3 worldPosition;
layout(location=8) out vec3 shadowPosition;
layout(location=9) noperspective out vec2 screenPos;
layout(location=10) out vec4 fogFactors;
layout(set=1,binding=0,std140) uniform SunLighting {
    vec4 normal0; vec4 normal1; vec4 normal2;
    vec4 direction; vec4 sunColor; vec4 ambient;
    vec4 projection; vec4 extra;
    vec4 surfaceParameters; vec4 surfaceEye;
    vec4 world0; vec4 world1; vec4 world2;
    vec4 shadow0; vec4 shadow1; vec4 shadow2; vec4 shadowParams;
    vec4 skyEye; vec4 skyTint; vec4 skyGlow; vec4 skyGrade; vec4 skyBlend;
    vec4 detail; vec4 detailMotion;
 vec4 weather; vec4 weatherFog;
 vec4 emissionParams; vec4 emissionRegions[32];
 vec4 geometryFog0; vec4 geometryFog1;
 uvec4 tiledLights;
 vec4 pomParams; vec4 pomUV; vec4 pomAtlas;
 uvec4 pomPolicy;
} sun;
layout(push_constant) uniform ModelPush {
    vec4 target; vec4 fogColor; vec4 factor; uvec4 mode;
    vec4 camera0; vec4 camera1; vec4 camera2; vec4 projection;
} draw;
void main() {
    vec4 p = vec4(position, 1.0);
    vec3 camera = vec3(dot(draw.camera0,p), dot(draw.camera1,p), dot(draw.camera2,p));
    worldPosition = vec3(dot(sun.world0,p), dot(sun.world1,p), dot(sun.world2,p));
    worldNormal = vec3(dot(sun.normal0.xyz,normal), dot(sun.normal1.xyz,normal), dot(sun.normal2.xyz,normal));
    shadowPosition = worldPosition;
    // Homogeneous projection avoids division by camera.z, including crossings
    // of the eye plane. Fixed-function clipping owns the resulting triangles.
    float w = camera.z / draw.target.z;
    vec2 centre = (draw.projection.zw + vec2(0.5)) / draw.target.xy * 2.0 - 1.0;
    vec2 clipXY = camera.xy * draw.projection.xy / draw.target.xy * 2.0 + centre * w;
    gl_Position = vec4(clipXY, 1.0, w);
    radialScreen = gl_Position.xyw;
    radialEye = vec4(camera, float(draw.mode.x >> 16));
    gl_ClipDistance[0] = camera.z - max(draw.target.z, draw.factor.a);
    gl_ClipDistance[1] = draw.target.w - camera.z;
    gl_PointSize = 1.0;
    screenPos = clipXY / max(w, 1e-20);
    uvPerspective = uvAffine = uv;
    // Prepared draws set flag 256 and carry node opacity in mode.w. Native draws
    // keep that word for two-sided normal orientation and stay opaque.
    float alpha = 1.0;
    if ((draw.mode.x & 256u) != 0u) alpha = uintBitsToFloat(draw.mode.w);
    colorSmooth = colorFlat = vec4((draw.mode.x & 4u) != 0u ? vec3(1.0) : draw.factor.rgb, alpha);
    fogFactors = vec4(0.0, 0.0, 0.0, 1.0);
    if (sun.geometryFog1.z > 0.5) {
        fogFactors.x = (length(camera.xz) - sun.geometryFog0.x) * sun.geometryFog0.y;
        fogFactors.y = 1.0 - (worldPosition.y - sun.geometryFog0.z) * sun.geometryFog0.w;
    }
    // geometryFog1.xy reuse spare components: edge start and inverse width.
    // This term also covers fog-off missions and terrain above the mission altitude band.
    // Cylindrical fog distance is separate from whole-cell/centre cull selection.
    fogFactors.z = (length(camera.xz) - sun.geometryFog1.x) * sun.geometryFog1.y;
    // Only the separate varying is unbounded; fragment consumers see clamped visibility.
    specularSmooth = specularFlat = vec4(0.0,0.0,0.0,1.0);
}
