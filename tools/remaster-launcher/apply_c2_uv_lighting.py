"""UV-local material emission and fixture placement; generated texture identities remain local.

Run on a fresh compatible private host. Supply its shader source and a local
c2_material_fixtures.inc, compile both shader variants, then rebuild the host.
This applicator never launches the game or publishes a launcher profile.
"""
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Add exact-material UV emission masks and UV-clipped fixture placement to a private native host.')
parser.add_argument('host',type=Path)
parser.add_argument('--backup',type=Path,required=True)
args=parser.parse_args()
host=args.host.resolve(strict=True);backup=args.backup.resolve()
if 'emission_regions{}' in (host/'fixture_lighting.hpp').read_text():
    raise SystemExit('UV fixture support already present; preserve the existing build and backups.')
backup.mkdir(parents=True,exist_ok=False)
files=['fixture_lighting.hpp','sun_lighting.hpp','sun_scene.frag','sun_scene_frag.h','effect_scene_frag.h','effect_lighting_stage.inc','d3d_provider.inc','vk_scene.hpp']
import shutil
for n in files:shutil.copy2(host/n,backup/n)
def edit(n,old,new):
 p=host/n;s=p.read_text();assert s.count(old)==1,(n,old[:90],s.count(old));p.write_text(s.replace(old,new))
edit('fixture_lighting.hpp','    bool is_spot;','    bool is_spot;\n    std::vector<std::array<float,4>> emission_regions{};\n    bool emission_only{false};')
edit('fixture_lighting.hpp','        // --- Remastered Texture Bank Entries ---','        #include "c2_material_fixtures.inc"\n        // --- Remastered Texture Bank Entries ---')
edit('fixture_lighting.hpp','    std::uint64_t source{};','    std::uint64_t source{};\n    std::uint64_t owner{};')
edit('fixture_lighting.hpp','return f.source==id;','return f.source==id||f.owner==id;')
# UV triangles are actual recorded vertices, not guessed world coordinates.
method=r'''
    struct UvPoint { Point p; float u,v; };
    void observe_regions(const FixtureDef& def,const std::vector<UvPoint>& triangles,unsigned frame,std::uint64_t owner){
        if(def.emission_only||def.radius<=0)return;
        for(size_t island=0;island<def.emission_regions.size();++island){
            const auto& rect=def.emission_regions[island];float best=0;Point position{},normal{};
            for(size_t at=0;at+2<triangles.size();at+=3){
                const auto&a=triangles[at];const auto&b=triangles[at+1];const auto&c=triangles[at+2];
                std::vector<UvPoint> poly{a,b,c};
                for(unsigned edge=0;edge<4&&!poly.empty();++edge){std::vector<UvPoint> clipped;
                    auto distance=[&](const UvPoint& p){return edge==0?p.u-rect[0]:edge==1?rect[2]-p.u:edge==2?p.v-rect[1]:rect[3]-p.v;};
                    auto previous=poly.back();float dp=distance(previous);
                    for(const auto& current:poly){const float dc=distance(current);
                        if((dp>=0)!=(dc>=0)){const float t=dp/(dp-dc);UvPoint cross{};for(unsigned j=0;j<3;++j)cross.p[j]=previous.p[j]+t*(current.p[j]-previous.p[j]);cross.u=previous.u+t*(current.u-previous.u);cross.v=previous.v+t*(current.v-previous.v);clipped.push_back(cross);}
                        if(dc>=0)clipped.push_back(current);previous=current;dp=dc;
                    }poly=std::move(clipped);
                }
                if(poly.size()<3)continue;float area=0;for(size_t i=0;i<poly.size();++i){const auto&p=poly[i];const auto&q=poly[(i+1)%poly.size()];area+=p.u*q.v-q.u*p.v;}area=std::abs(area);
                if(area<=best||area<1e-10f)continue;best=area;position={};for(const auto&p:poly)for(unsigned j=0;j<3;++j)position[j]+=p.p[j]/float(poly.size());
                Point e{},f{};for(unsigned j=0;j<3;++j){e[j]=b.p[j]-a.p[j];f[j]=c.p[j]-a.p[j];}normal={e[1]*f[2]-e[2]*f[1],e[2]*f[0]-e[0]*f[2],e[0]*f[1]-e[1]*f[0]};
            }
            const float length=std::sqrt(effects::distance2(normal,{0,0,0}));if(best<=0||length<=1e-6f)continue;
            for(unsigned j=0;j<3;++j){normal[j]/=length;position[j]+=normal[j]*def.normal_offset;}
            const std::uint64_t id=owner?(owner^(0x9e3779b97f4a7c15ULL*(island+1))):0;
            bool updated=false;for(auto&old:fixtures_)if((id&&old.source==id)||(!id&&!old.source&&old.def==&def&&effects::distance2(old.position,position)<.0625f)){old={position,normal,&def,frame,id,owner};updated=true;break;}
            if(!updated&&fixtures_.size()<512)fixtures_.push_back({position,normal,&def,frame,id,owner});
        }
    }
'''
edit('fixture_lighting.hpp','    size_t active_count()const{return fixtures_.size();}',method+'\n    size_t active_count()const{return fixtures_.size();}')
from fix_fixture_uv_anchor import apply as anchor_fixture_uv
anchor_fixture_uv(host/'fixture_lighting.hpp')
edit('sun_lighting.hpp','static_assert(sizeof(Uniform)==384);','static_assert(sizeof(Uniform)==912);')
edit('sun_lighting.hpp','    std::array<float,4> weather{},weather_fog{};','    std::array<float,4> emission_params{};\n    std::array<std::array<float,4>,32> emission_regions{};\n    std::array<float,4> weather{},weather_fog{};')
# Keep the existing 384-byte uniform prefix byte-for-byte; new fields must follow weather.
p=host/'sun_lighting.hpp';s=p.read_text();s=s.replace('    std::array<float,4> emission_params{};\n    std::array<std::array<float,4>,32> emission_regions{};\n    std::array<float,4> weather{},weather_fog{};','    std::array<float,4> weather{},weather_fog{};');s=s.replace('};\nstatic_assert(sizeof(Uniform)==912);','    std::array<float,4> emission_params{};\n    std::array<std::array<float,4>,32> emission_regions{};\n};\nstatic_assert(sizeof(Uniform)==912);');p.write_text(s)
edit('vk_scene.hpp','bool condition_schematic{}; };','bool condition_schematic{};std::array<float,4> emission_params{};std::array<std::array<float,4>,32> emission_regions{}; };')
edit('vk_scene.hpp','std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)+at*sunStride,&u,sizeof(u));sunScene=true;','u.emission_params=draw.emission_params;u.emission_regions=draw.emission_regions;\n                std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)+at*sunStride,&u,sizeof(u));sunScene=true;')
old='if(const auto*fixture=fixture_of(*surface)){pu.fog[3]=1.0f+fixture->intensity;}'
new='''if(const auto*fixture=fixture_of(*surface)){pu.fog[3]=1.0f+fixture->intensity;
    if(!fixture->emission_regions.empty()){const auto count=std::min(size_t(32),fixture->emission_regions.size());dr.emission_params={float(count),fixture->intensity,0,0};for(size_t i=0;i<count;++i)dr.emission_regions[i]=fixture->emission_regions[i];}}'''
edit('d3d_provider.inc',old,new)
# Route exact UV islands through actual triangle topology, retaining the legacy catalog route.
old='  mw34::fixtures::FixtureManager::instance().observe_polygon(*fixture, fix_pts, host.frames,fixture_source(draw,*surface));'
new=r'''  auto& manager=mw34::fixtures::FixtureManager::instance();const auto source=fixture_source(draw,*surface);
  if(fixture->emission_regions.empty())manager.observe_polygon(*fixture,fix_pts,host.frames,source);
  else if(!fixture->emission_only){
   std::vector<mw34::fixtures::FixtureManager::UvPoint> vertices,triangles;
   if(draw.model&&draw.model->world&&draw.model->sun_eligible){const auto&m=draw.model->sun_world;for(const auto&v:draw.model->geometry->vertices)vertices.push_back({{m[0]*v.x+m[1]*v.y+m[2]*v.z+m[3],m[4]*v.x+m[5]*v.y+m[6]*v.z+m[7],m[8]*v.x+m[9]*v.y+m[10]*v.z+m[11]},v.u,v.v});triangles=vertices;}
   else{for(size_t i=0;i<points.size();++i){Vertex v;std::memcpy(&v,draw.vertices.data()+i*32,32);vertices.push_back({{points[i][0],points[i][1],points[i][2]},v.u,v.v});}
    const size_t count=draw.indices.empty()?vertices.size():draw.indices.size();auto add=[&](size_t i){const size_t k=draw.indices.empty()?i:draw.indices[i];if(k>=vertices.size())throw std::runtime_error("Fixture UV index outside captured vertices");triangles.push_back(vertices[k]);};
    if(draw.flags==D3DPT_TRIANGLELIST){for(size_t i=0;i+2<count;i+=3){add(i);add(i+1);add(i+2);}}
    else if(draw.flags==D3DPT_TRIANGLEFAN){for(size_t i=1;i+1<count;++i){add(0);add(i);add(i+1);}}
    else if(draw.flags==D3DPT_TRIANGLESTRIP){for(size_t i=0;i+2<count;++i){add(i);add(i+(i&1?2:1));add(i+(i&1?1:2));}}
   }
   manager.observe_regions(*fixture,triangles,host.frames,source);
  }'''
edit('effect_lighting_stage.inc',old,new)
edit('sun_scene.frag',' vec4 weather; vec4 weatherFog;',' vec4 weather; vec4 weatherFog;\n vec4 emissionParams; vec4 emissionRegions[32];')
edit('sun_scene.frag','        float bulb = smoothstep(0.55, 0.9, lum);',r'''        float bulb = smoothstep(0.55, 0.9, lum);
        if(sun.emissionParams.x>0.5){
            float mask=0.0;vec2 t=fract(uv);vec2 feather=max(fwidth(t),vec2(0.0005));
            for(int i=0;i<min(int(sun.emissionParams.x),32);++i){vec4 r=sun.emissionRegions[i];vec2 low=smoothstep(r.xy-feather,r.xy+feather,t);vec2 high=1.0-smoothstep(r.zw-feather,r.zw+feather,t);mask=max(mask,low.x*low.y*high.x*high.y);}
            bulb=mask*smoothstep(0.20,0.70,max(texel.r,max(texel.g,texel.b)));
        }''')
print('Applied UV-clipped lamp placement and bounded per-material emission regions to active host sources. Executable unchanged pending build.')


edit('effect_lighting_stage.inc','  for(size_t at=0;at<draw.vertices.size();at+=32){Vertex v;std::memcpy(&v,draw.vertices.data()+at,32);points.push_back(mw34::effects::reconstruct(v.x,v.y,v.z,s.projection,s.camera));}','  if(draw.model&&draw.model->world&&draw.model->sun_eligible){const auto&m=draw.model->sun_world;for(const auto&v:draw.model->geometry->vertices)points.push_back({m[0]*v.x+m[1]*v.y+m[2]*v.z+m[3],m[4]*v.x+m[5]*v.y+m[6]*v.z+m[7],m[8]*v.x+m[9]*v.y+m[10]*v.z+m[11]});}\n  else for(size_t at=0;at<draw.vertices.size();at+=32){Vertex v;std::memcpy(&v,draw.vertices.data()+at,32);points.push_back(mw34::effects::reconstruct(v.x,v.y,v.z,s.projection,s.camera));}')
