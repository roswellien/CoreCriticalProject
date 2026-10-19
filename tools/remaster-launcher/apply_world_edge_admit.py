"""Keep screen-edge-clipped world polygons on the GPU world path; optional vsync off.

The GPU world path draws a polygon from its retained original geometry only
when the game submits it unclipped. Polygons crossing the screen sides are
clipped by the original CPU code first, fall back to transformed-and-lit (TL)
triangles and are lit differently (reconstructed face normals vs mesh
normals), so shading changed at the screen edges while turning.

MW34_WORLD_EDGE_ADMIT=1 (sun builds only): when every submitted vertex lies on
the original polygon's plane and every original corner is between the near
and far limits, the polygon was clipped by the screen sides only. Its
submission is rebuilt from the original corners (UVs from the geometry,
vertex fog fitted linearly in depth from the clipped vertices) and it takes
the GPU path; the viewport performs the same side clipping. Near-plane cuts
keep the original fallback.

MW34_VSYNC=0 presents with IMMEDIATE (else MAILBOX) instead of FIFO.
Apply after the other sun/shadow/atmosphere host edits.
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one edge-admit anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

ADMIT = r'''
bool world_edge_enabled(){static const bool on=[]{const char*p=std::getenv("MW34_WORLD_EDGE_ADMIT");return p&&*p=='1';}();return on;}
std::uint64_t world_edge_admits{},world_edge_rejects{};
bool world_edge_admit(D3DCmd& draw,const WorldPolygon& polygon,const OverrideMatrix& m,double near_scale,double sx,double sy,double cx,double cy,double near_clip){
 if(!world_edge_enabled()||!mw34::sun::settings().enabled)return false;
 struct Tl {float x,y,z,rhw;unsigned color,spec;float u,v;};
 const unsigned n=unsigned(polygon.corners.size()),k=unsigned(draw.vertices.size()/32);
 if(n<3||k<3||n>64)return false;
 const unsigned camera=load(0x7402f4);if(!camera||!readable(camera+0xb4,4))return false;
 const double far_limit=wide_float(camera+0xb4);if(!(far_limit>near_clip))return false;
 std::vector<std::array<double,3>> cam(n);
 for(unsigned j=0;j<n;++j){const auto&v=polygon.corners[n-1-j].vertex;
  cam[j]={m[0]*v.x+m[1]*v.y+m[2]*v.z+m[3],m[4]*v.x+m[5]*v.y+m[6]*v.z+m[7],m[8]*v.x+m[9]*v.y+m[10]*v.z+m[11]};
  if(!(cam[j][2]>near_clip*1.001)||!(cam[j][2]<far_limit*0.999)){++world_edge_rejects;return false;}}
 std::array<double,3> nrm{0,0,0},c0{0,0,0};
 for(unsigned j=0;j<n;++j){const auto&a=cam[j];const auto&b=cam[(j+1)%n];
  nrm[0]+=(a[1]-b[1])*(a[2]+b[2]);nrm[1]+=(a[2]-b[2])*(a[0]+b[0]);nrm[2]+=(a[0]-b[0])*(a[1]+b[1]);for(unsigned i=0;i<3;++i)c0[i]+=a[i]/n;}
 const double nl=std::sqrt(nrm[0]*nrm[0]+nrm[1]*nrm[1]+nrm[2]*nrm[2]);if(!(nl>1e-12))return false;
 std::vector<Tl> in(k);double sz=0,sf=0,szz=0,szf=0;unsigned cnt=0,ones=0,zeros=0;
 for(unsigned i=0;i<k;++i){std::memcpy(&in[i],draw.vertices.data()+i*32,32);const auto&t=in[i];
  if(!std::isfinite(t.x)||!std::isfinite(t.y)||!std::isfinite(t.rhw)||!(t.rhw>0)){++world_edge_rejects;return false;}
  const double p[3]={(t.x-cx)/(sx*t.rhw),(t.y-cy)/(sy*t.rhw),near_scale/t.rhw};
  const double d=((p[0]-c0[0])*nrm[0]+(p[1]-c0[1])*nrm[1]+(p[2]-c0[2])*nrm[2])/nl;
  if(!std::isfinite(d)||std::abs(d)>std::max(0.02,p[2]*2e-3)){++world_edge_rejects;return false;}
  const unsigned fa=t.spec>>24;if(fa>=255)++ones;else if(!fa)++zeros;else{const double f=fa/255.0;sz+=p[2];sf+=f;szz+=p[2]*p[2];szf+=p[2]*f;++cnt;}}
 // Vertex fog (specular alpha): linear in depth from the unclamped clipped vertices.
 double fa=1,fb=0;
 if(cnt>=2&&std::abs(cnt*szz-sz*sz)>1e-9){fb=(cnt*szf-sz*sf)/(cnt*szz-sz*sz);fa=(sf-fb*sz)/cnt;}
 else if(cnt)fa=sf/cnt;
 else if(ones&&!zeros)fa=1;else if(zeros&&!ones)fa=0;else{++world_edge_rejects;return false;}
 std::vector<unsigned char> out(size_t(n)*32);
 for(unsigned j=0;j<n;++j){const auto&v=polygon.corners[n-1-j].vertex;Tl t;const double r=near_scale/cam[j][2];
  t.x=float(cam[j][0]*sx*r+cx);t.y=float(cam[j][1]*sy*r+cy);t.z=t.rhw=float(r);t.color=in[0].color;
  const double f=std::min(1.0,std::max(0.0,fa+fb*cam[j][2]));t.spec=(in[0].spec&0xffffffu)|(unsigned(std::lround(f*255))<<24);
  t.u=v.u;t.v=v.v;std::memcpy(out.data()+size_t(j)*32,&t,32);}
 draw.vertices=std::move(out);++world_edge_admits;return true;
}
'''

def apply(host):
    w=host/'world_direct_stage.inc'
    text=w.read_text()
    if 'world_edge_admit' in text:raise RuntimeError('Use a fresh host copy; edge admission already installed')
    anchor='void world_capture(D3DCmd&draw){'
    edit(w,anchor,ADMIT.strip()+'\n'+anchor)
    edit(w,' if(count<3||polygon.corners.size()!=count){++world_misses;return;}',' if(count<3){++world_misses;return;}bool exact=polygon.corners.size()==count;')
    edit(w,' for(unsigned j=0;j<count;++j){const auto&v=polygon.corners[count-1-j].vertex;Tl tl;',' if(exact)for(unsigned j=0;j<count;++j){const auto&v=polygon.corners[count-1-j].vertex;Tl tl;')
    t=w.read_text()
    a=t.index(' if(exact)for(unsigned j=0;j<count;++j)');b=t.index(' auto instance=std::make_shared<mw34::vkscene::ModelInstance>();instance->geometry=polygon.resident;',a)
    block=t[a:b].replace('{++world_misses;return;}','{exact=false;break;}')
    block=block.rstrip()+'\n if(!exact&&!world_edge_admit(draw,polygon,matrix,near_scale,sx,sy,cx,cy,near_clip)){++world_misses;return;}\n'
    w.write_text(t[:a]+block+t[b:])
    edit(host/'world_geometry_stage.inc','<<",\\\"unmatched\\\":"<<world_misses','<<",\\\"edge_admits\\\":"<<world_edge_admits<<",\\\"edge_rejects\\\":"<<world_edge_rejects<<",\\\"unmatched\\\":"<<world_misses')
    vk=host/'vk_scene.hpp'
    edit(vk,'X(vkGetPhysicalDeviceSurfaceFormatsKHR)','X(vkGetPhysicalDeviceSurfaceFormatsKHR) X(vkGetPhysicalDeviceSurfacePresentModesKHR)')
    edit(vk,'        sc.presentMode = VK_PRESENT_MODE_FIFO_KHR; sc.clipped = VK_TRUE;','''        sc.presentMode = VK_PRESENT_MODE_FIFO_KHR; sc.clipped = VK_TRUE;
        if (const char *vs = std::getenv("MW34_VSYNC"); vs && !std::strcmp(vs, "0") && f.vkGetPhysicalDeviceSurfacePresentModesKHR) {
            unsigned pm = 0; f.vkGetPhysicalDeviceSurfacePresentModesKHR(gpu, windowSurface, &pm, nullptr);
            std::vector<VkPresentModeKHR> modes(pm); f.vkGetPhysicalDeviceSurfacePresentModesKHR(gpu, windowSurface, &pm, modes.data());
            auto has = [&](VkPresentModeKHR m) { return std::find(modes.begin(), modes.end(), m) != modes.end(); };
            sc.presentMode = has(VK_PRESENT_MODE_IMMEDIATE_KHR) ? VK_PRESENT_MODE_IMMEDIATE_KHR : has(VK_PRESENT_MODE_MAILBOX_KHR) ? VK_PRESENT_MODE_MAILBOX_KHR : VK_PRESENT_MODE_FIFO_KHR;
            static bool told = false; if (!told) { told = true; std::fprintf(stderr, "Vsync off: present mode %s\\n", sc.presentMode == VK_PRESENT_MODE_IMMEDIATE_KHR ? "IMMEDIATE" : sc.presentMode == VK_PRESENT_MODE_MAILBOX_KHR ? "MAILBOX" : "FIFO (no alternative)"); }
        }''')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
