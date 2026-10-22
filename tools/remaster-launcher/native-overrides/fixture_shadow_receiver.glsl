layout(set=1,binding=3) uniform sampler2D fixtureShadowAtlas;
float fixtureVisibility(int index,vec3 p,vec3 n){
 vec4 meta=effects.shadowMeta[index];if(meta.x<0.5)return 1.0;
 vec3 d=p+n*meta.w-effects.lights[index].start.xyz;
 vec3 magnitude=abs(d),facePosition;int face;
 if(magnitude.x>=magnitude.y&&magnitude.x>=magnitude.z){
  if(d.x>=0.0){face=0;facePosition=vec3(-d.z,-d.y,d.x);}
  else{face=1;facePosition=vec3(d.z,-d.y,-d.x);}
 }else if(magnitude.y>=magnitude.z){
  if(d.y>=0.0){face=2;facePosition=vec3(d.x,d.z,d.y);}
  else{face=3;facePosition=vec3(d.x,-d.z,-d.y);}
 }else{
  if(d.z>=0.0){face=4;facePosition=vec3(d.x,-d.y,d.z);}
  else{face=5;facePosition=vec3(-d.x,-d.y,-d.z);}
 }
 float nearPlane=meta.y,farPlane=meta.z;
 if(facePosition.z<=nearPlane||facePosition.z>=farPlane)return 1.0;
 float reference=farPlane/(farPlane-nearPlane)-farPlane*nearPlane/((farPlane-nearPlane)*facePosition.z)-0.00005;
 int tile=index*6+face;ivec2 atlas=textureSize(fixtureShadowAtlas,0);
 vec2 size=vec2(atlas)/vec2(16,24),origin=vec2(tile%16,tile/16)*size;
 vec2 local=(facePosition.xy/facePosition.z*.5+.5)*size;
 float visibility=0.0;
 for(int y=0;y<2;++y)for(int x=0;x<2;++x){
  vec2 pixel=origin+clamp(local+vec2(x,y)-.5,vec2(.5),size-.5);
  visibility+=reference<=texture(fixtureShadowAtlas,pixel/vec2(atlas)).r?1.0:0.0;
 }
 return visibility*.25;
}
