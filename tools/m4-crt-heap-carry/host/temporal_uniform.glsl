layout(set=1,binding=0,std140) uniform Temporal {
    vec4 camera0;vec4 camera1;vec4 camera2;
    vec4 world0;vec4 world1;vec4 world2;
    vec4 previous0;vec4 previous1;vec4 previous2;
    vec4 projection;vec4 previousProjection;vec4 dimensions;
    vec4 depth;vec4 previous;vec4 jitter;uvec4 flags;
} temporal;
