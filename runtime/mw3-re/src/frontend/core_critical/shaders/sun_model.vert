#version 450
// Optional replacement geometry only. Original TL vertices keep their shader.
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


// First 64 bytes match the unmodified fragment shader's Push ABI.
// target = (guestWidth, guestHeight, nearScale, nearClip).
// factor = the batch RGB colour; override draw arguments use TEXTURE/DIFFUSE,
// so the fragment shader never selects D3DTA_TFACTOR for a model draw.
// projection = (scaleX, scaleY, centerX, centerY).
layout(push_constant) uniform ModelPush {
    vec4 target;
    vec4 fogColor;
    vec4 factor;
    uvec4 mode;
    vec4 camera0;
    vec4 camera1;
    vec4 camera2;
    vec4 projection;
} draw;

void main() {
    vec4 p = vec4(position, 1.0);
    worldPosition = vec3(dot(sun.world0, p), dot(sun.world1, p), dot(sun.world2, p));
    shadowPosition = worldPosition;
    worldNormal = vec3(dot(sun.normal0.xyz, normal), dot(sun.normal1.xyz, normal), dot(sun.normal2.xyz, normal));
    precise vec3 camera = vec3(dot(draw.camera0, p), dot(draw.camera1, p), dot(draw.camera2, p));
    vec3 rgb=draw.factor.rgb;
    precise float rhw = draw.target.z / camera.z;
    precise vec2 screen = camera.xy * draw.projection.xy * rhw + draw.projection.zw;
    float w = 1.0 / rhw;
    vec2 ndc = (screen + 0.5) / draw.target.xy * 2.0 - 1.0;
    gl_Position = vec4(ndc * w, rhw * w, w);
    radialScreen = gl_Position.xyw;
    radialEye = vec4(camera, float(draw.mode.x >> 16));
    screenPos = screen;
    gl_PointSize = 1.0;
    uvPerspective = uvAffine = uv;
    colorSmooth = colorFlat = vec4(rgb, uintBitsToFloat(draw.mode.w));
    fogFactors = vec4(0.0, 0.0, 0.0, 1.0);
    if (sun.geometryFog1.z > 0.5) {
        fogFactors.x = (length(camera.xz) - sun.geometryFog0.x) * sun.geometryFog0.y;
        fogFactors.y = 1.0 - (worldPosition.y - sun.geometryFog0.z) * sun.geometryFog0.w;
    }
    // Same packed edge band as native_geometry.vert; no altitude dependence.
    fogFactors.z = (length(camera.xz) - sun.geometryFog1.x) * sun.geometryFog1.y;
    specularSmooth = specularFlat = vec4(0.0, 0.0, 0.0, 1.0);
}
