#version 450
#extension GL_GOOGLE_include_directive : require
#include "temporal_uniform.glsl"
layout(location=0) in vec2 uvPerspective;
layout(location=1) noperspective in vec2 uvAffine;
layout(location=2) noperspective in vec4 colorSmooth;
layout(location=3) flat in vec4 colorFlat;
layout(location=4) noperspective in vec4 specularSmooth;
layout(location=5) flat in vec4 specularFlat;
layout(location=6) in vec3 cameraPoint;
layout(location=7) in vec3 worldPoint;
layout(set=0,binding=0) uniform sampler2D image;
layout(push_constant) uniform Push {vec4 target;vec4 fogColor;vec4 factor;uvec4 mode;} draw;
layout(location=0) out float depthOutput;
layout(location=1) out vec2 motionOutput;
layout(location=2) out float validityOutput;
#include "fragment_alpha.glsl"
void main(){
    uint flags=draw.mode.x;
    diffuse=(flags&1u)!=0u?colorFlat:colorSmooth;
    specular=(flags&1u)!=0u?specularFlat:specularSmooth;
    vec2 uv=(flags&2u)!=0u?uvPerspective:uvAffine;
    texel=(flags&4u)!=0u?texture(image,uv):vec4(1.0);
    float alpha=clamp(operation(draw.mode.z).a,0.0,1.0);
    reject_alpha(alpha);
    // Source-over at zero alpha preserves destination color. With no depth
    // writes, it also preserves the existing surface's temporal metadata.
    if(temporal.flags.z!=0u && alpha==0.0)discard;
    depthOutput=0.0;motionOutput=vec2(0);validityOutput=0.0;
    if(temporal.flags.x==0u)return;
    if(cameraPoint.z<=temporal.depth.y || cameraPoint.z>temporal.depth.z)return;
    depthOutput=temporal.depth.y/cameraPoint.z;
    if(temporal.flags.y==0u)return;
    vec4 world=vec4(worldPoint,1.0);
    vec3 before=vec3(dot(temporal.previous0,world),dot(temporal.previous1,world),dot(temporal.previous2,world));
    if(before.z<=temporal.depth.w || before.z>temporal.previous.w)return;
    vec2 currentScreen=cameraPoint.xy*temporal.projection.xy*(temporal.depth.x/cameraPoint.z)+temporal.projection.zw;
    vec2 previousScreen=before.xy*temporal.previousProjection.xy*(temporal.previous.x/before.z)+temporal.previousProjection.zw;
    vec2 currentPixel=(currentScreen+0.5)*temporal.dimensions.zw/temporal.dimensions.xy;
    vec2 previousPixel=(previousScreen+0.5)*temporal.dimensions.zw/temporal.previous.yz;
    if(any(lessThan(previousPixel,vec2(0))) || any(greaterThanEqual(previousPixel,temporal.dimensions.zw)))return;
    vec2 motion=previousPixel-currentPixel;
    if(any(isnan(motion)) || any(isinf(motion)) || any(greaterThan(abs(motion),temporal.dimensions.zw)))return;
    motionOutput=motion;validityOutput=1.0;
}
