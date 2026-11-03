#version 450
// Static opaque producer: resident geometry and original vertex fog. Modern
// per-pixel lighting owns RGB, as in the existing lit resident-world shader.
layout(location=0) in vec3 position;
layout(location=1) in vec3 normal;
layout(location=2) in vec2 uv;
layout(location=0) out vec2 uvPerspective;
layout(location=1) noperspective out vec2 uvAffine;
layout(location=2) noperspective out vec4 colorSmooth;
layout(location=3) flat out vec4 colorFlat;
layout(location=4) noperspective out vec4 specularSmooth;
layout(location=5) flat out vec4 specularFlat;
layout(location=6) out vec3 worldNormal;
layout(location=7) out vec3 worldPosition;
layout(location=8) out vec3 shadowPosition;
layout(location=9) noperspective out vec2 screenPos;

layout(set=1,binding=0,std140) uniform StaticLighting {
    layout(offset=0) vec4 normal0;
    vec4 normal1; vec4 normal2;
    layout(offset=128) vec4 world0;
    vec4 world1; vec4 world2;
    // Appended to sun::Uniform; the established first 912 bytes retain their ABI.
    layout(offset=912) vec4 fogDistance;
    vec4 fogHeight;
    vec4 fogHeightRow;
} lighting;
layout(push_constant) uniform ModelPush {
    vec4 target; vec4 fogColor; vec4 factor; uvec4 mode;
    vec4 camera0; vec4 camera1; vec4 camera2; vec4 projection;
} draw;

float fogCoefficient(vec3 p) {
    if (lighting.fogHeight.w == 0.0) return 0.0;
    precise double radiusSum = double(p.x)*double(p.x) + double(p.z)*double(p.z);
    float radiusSquared = float(radiusSum);
    if (radiusSquared <= lighting.fogDistance.y) return 0.0;
    precise double heightSum = double(p.x)*double(lighting.fogHeightRow.x)
                            + double(p.y)*double(lighting.fogHeightRow.y);
    heightSum = heightSum + double(p.z)*double(lighting.fogHeightRow.z);
    heightSum = heightSum + double(lighting.fogHeightRow.w);
    float height = float(heightSum);
    if (height >= lighting.fogHeight.x) return 0.0;
    float fog;
    if (radiusSquared < lighting.fogDistance.z) {
        // Preserve the original exponent-based square-root approximation.
        float radius = uintBitsToFloat((floatBitsToUint(radiusSquared)>>1)+0x1fc00000u);
        precise double ramp = (double(radius)-double(lighting.fogDistance.x))*double(lighting.fogDistance.w);
        float distanceFog = float(ramp);
        fog = distanceFog;
        if (height > lighting.fogHeight.y) {
            precise double heightFog = (double(lighting.fogHeight.x)-double(height))*double(lighting.fogHeight.z);
            heightFog = heightFog*double(distanceFog);
            fog = float(heightFog);
        }
    } else if (height <= lighting.fogHeight.y) {
        fog = 1.0;
    } else {
        precise double heightFog = (double(lighting.fogHeight.x)-double(height))*double(lighting.fogHeight.z);
        fog = float(heightFog);
    }
    return clamp(fog, 0.0, 1.0);
}

void main() {
    vec4 p = vec4(position, 1.0);
    worldPosition = vec3(dot(lighting.normal0,p),dot(lighting.normal1,p),dot(lighting.normal2,p));
    shadowPosition = vec3(dot(lighting.world0,p),dot(lighting.world1,p),dot(lighting.world2,p));
    worldNormal = vec3(dot(lighting.normal0.xyz,normal),dot(lighting.normal1.xyz,normal),dot(lighting.normal2.xyz,normal));
    // Raster position retains the existing resident-world calculation.
    precise vec3 camera = vec3(dot(draw.camera0,p),dot(draw.camera1,p),dot(draw.camera2,p));
    precise float rhw = draw.target.z/camera.z;
    precise vec2 screen = camera.xy*draw.projection.xy*rhw+draw.projection.zw;
    float w = 1.0/rhw;
    vec2 ndc = (screen+0.5)/draw.target.xy*2.0-1.0;
    gl_Position = vec4(ndc*w,rhw*w,w);
    gl_PointSize = 1.0;
    screenPos = screen;
    uvPerspective = uvAffine = uv;
    colorSmooth = colorFlat = vec4(1.0);
    // Original CPU fog used stored float32 camera coordinates, not raster dot products.
    precise dvec3 legacyCamera;
    legacyCamera.x = double(position.x)*double(draw.camera0.x)+double(position.y)*double(draw.camera0.y);
    legacyCamera.x = legacyCamera.x+double(position.z)*double(draw.camera0.z);
    legacyCamera.x = legacyCamera.x+double(draw.camera0.w);
    legacyCamera.y = double(position.x)*double(draw.camera1.x)+double(position.y)*double(draw.camera1.y);
    legacyCamera.y = legacyCamera.y+double(position.z)*double(draw.camera1.z);
    legacyCamera.y = legacyCamera.y+double(draw.camera1.w);
    legacyCamera.z = double(position.x)*double(draw.camera2.x)+double(position.y)*double(draw.camera2.y);
    legacyCamera.z = legacyCamera.z+double(position.z)*double(draw.camera2.z);
    legacyCamera.z = legacyCamera.z+double(draw.camera2.w);
    float fog = fogCoefficient(vec3(legacyCamera));
    precise double packedFog = 255.5-double(fog)*255.0;
    uint alpha = uint(clamp(packedFog,0.0,255.0));
    specularSmooth = specularFlat = vec4(0.0,0.0,0.0,float(alpha)/255.0);
}
