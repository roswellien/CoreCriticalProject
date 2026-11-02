#version 450
#extension GL_GOOGLE_include_directive : require
#include "temporal_uniform.glsl"
layout(location=0) in vec4 position;
layout(location=1) in uint diffuse;
layout(location=2) in uint specular;
layout(location=3) in vec2 uv;
layout(location=0) out vec2 uvPerspective;
layout(location=1) noperspective out vec2 uvAffine;
layout(location=2) noperspective out vec4 colorSmooth;
layout(location=3) flat out vec4 colorFlat;
layout(location=4) noperspective out vec4 specularSmooth;
layout(location=5) flat out vec4 specularFlat;
layout(location=6) out vec3 cameraPoint;
layout(push_constant) uniform Push {vec4 target;vec4 fogColor;vec4 factor;uvec4 mode;} draw;
vec4 unpack(uint c){return vec4((c>>16)&255u,(c>>8)&255u,c&255u,c>>24)/255.0;}
void main(){
    vec4 local=vec4(position.xyz,1.0);
    vec2 screen;float reciprocal,w;
    if(temporal.flags.x!=0u){
        cameraPoint=vec3(dot(temporal.camera0,local),dot(temporal.camera1,local),dot(temporal.camera2,local));
        reciprocal=temporal.depth.x/cameraPoint.z;
        screen=cameraPoint.xy*temporal.projection.xy*reciprocal+temporal.projection.zw;
        w=1.0/reciprocal;
    }else{
        screen=position.xy;reciprocal=position.z;w=position.w!=0.0?1.0/position.w:1.0;
        cameraPoint=vec3(0);
    }
    vec2 pixel=(screen+0.5)*temporal.dimensions.zw/temporal.dimensions.xy+temporal.jitter.xy;
    gl_Position=vec4((pixel/temporal.dimensions.zw*2.0-1.0)*w,reciprocal*w,w);
    gl_PointSize=1.0;uvPerspective=uvAffine=uv;
    colorSmooth=colorFlat=unpack(diffuse);specularSmooth=specularFlat=unpack(specular);
}
