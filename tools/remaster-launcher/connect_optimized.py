"""Snapshot the current optimized native host and connect existing Remaster adapters."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[2]
CURRENT=ROOT/'tools/m4-crt-heap-carry'
ASSET=ROOT/'local/work-ahead/mw3-cinematic-mechs-r1/runtime-integration-r1/host-source'
OUT=ROOT/'local/remaster/optimized-native-r1'
HOST=OUT/'host-source'
if HOST.exists():raise RuntimeError('Preserve existing snapshot; choose a new revision')
HOST.mkdir(parents=True)
pins={}
for p in CURRENT.iterdir():
    if p.suffix in {'.h','.hpp','.cpp','.inc'}:
        shutil.copy2(p,HOST/p.name);pins[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copytree(CURRENT/'memory',HOST/'memory')
for name in ('mesh_override_stage.inc','override_source_roster.inc','override_new_rosters.inc','remaster_banks.inc','remaster_render.inc'):
    shutil.copy2(ASSET/name,HOST/name)

def replace(text,old,new):
    if text.count(old)!=1:raise RuntimeError('Source anchor changed: '+old[:100])
    return text.replace(old,new)

p=HOST/'mesh_override_stage.inc';s=p.read_text()
s=replace(s,'meshes.erase("left ski");meshes.erase("right ski");',
'''meshes.erase("left ski");meshes.erase("right ski");
 // Exclude only the complete observed original cockpit attachment, preserving its draws.
 const std::array<std::pair<const char*,unsigned>,13> cockpit{{{"cpit_ania",4},{"cpit_anib",4},{"cpit_anic",4},{"crack01",4},{"crack02",4},{"crack03",4},{"dbase",138},{"ding01",4},{"ding02",4},{"ding03",4},{"g40",54},{"hcrack01",3},{"hcrack02",3}}};
 bool attached_cockpit=true;for(const auto&c:cockpit){auto it=meshes.find(c.first);if(it==meshes.end()||it->second!=c.second){attached_cockpit=false;break;}}
 if(attached_cockpit)for(const auto&c:cockpit)meshes.erase(c.first);''')
p.write_text(s)

p=HOST/'mfc_stage.hpp';s=p.read_text()
s=replace(s,'unsigned texture{};};','unsigned texture{};int override_texture{-1};};')
pose=(ASSET/'pose_capture_stage.inc').read_text()
pose=pose[pose.index('std::string pose_name('):pose.index('PoseCaptureEntry pose_capture_begin(')]
s=replace(s,' void*enter(State*s',pose+'\n #include "mesh_override_stage.inc"\n #include "remaster_banks.inc"\n void*enter(State*s')
s=replace(s,'++bodies;return body(s,target,p);}',
    '++bodies;void*result=nullptr;if(target==0x53f2e0&&override_enabled()){auto previous=override_begin(state.gpr.rcx.dword);try{result=body(s,target,p);}catch(...){override_restore(previous);throw;}override_restore(previous);}else result=body(s,target,p);if(target==0x51fb30)override_emit();return result;}')
s=replace(s,'return pth.lexically_normal().make_preferred().string();',
    'return remaster_bank(pth.lexically_normal().make_preferred(),std::filesystem::path(game_dir()));')
s=replace(s,'RECT r{0,0,int(w)*sc,int(h)*sc};',
    'const unsigned rw=mw34::vkscene::Renderer::remaster_width(),rh=mw34::vkscene::Renderer::remaster_height();RECT r{0,0,rw?int(rw):int(w)*sc,rh?int(rh):int(h)*sc};')
p.write_text(s)

p=HOST/'d3d_provider.inc';s=p.read_text()
s=replace(s,'D3DDEVICEDESC hal_desc()const{','D3DDEVICEDESC hal_desc(){')
s=replace(s,'static_assert(sizeof(D3DDEVICEDESC)==252);',
'''static_assert(sizeof(D3DDEVICEDESC)==252);
 if(!host.renderer)host.renderer=std::make_unique<mw34::vkscene::Renderer>();unsigned max_texture{};
 try{HostInternal hi(*this);max_texture=host.renderer->max_texture_dimension();}catch(const std::exception&e){deny(std::string(e.what()),0);}''')
s=replace(s,'d.dwMaxTextureWidth=256;d.dwMaxTextureHeight=256;','d.dwMaxTextureWidth=max_texture;d.dwMaxTextureHeight=max_texture;')
s=replace(s,'dev->in_scene=true;return done(DD_OK,1);','dev->in_scene=true;override_scene_start();return done(DD_OK,1);')
s=replace(s,'c.texture=dev->textures[0];dev->commands.push_back(std::move(c));',
    'c.texture=dev->textures[0];if(!override_suppress_draw())dev->commands.push_back(std::move(c));')
old=(ASSET/'d3d_provider.inc').read_text()
start=old.index('  if(c.override_texture>=0)');end=old.index('else if(tex)',start)
replacement=old[start:end]+'else if(tex)'
s=replace(s,'if(tex){auto*t=vsurface(tex);',replacement+'{auto*t=vsurface(tex);')
s=replace(s,'|(tex?4U:0U)|','|((tex||c.override_texture>=0)?4U:0U)|')
p.write_text(s)

p=HOST/'vk_scene.hpp';s=p.read_text()
s=replace(s,'X(vkGetPhysicalDeviceProperties)','X(vkGetPhysicalDeviceProperties) X(vkGetPhysicalDeviceFeatures)')
s=replace(s,'std::uint64_t presents{};',
    'unsigned max_texture_dimension(){if(!device)init();VkPhysicalDeviceProperties p{};f.vkGetPhysicalDeviceProperties(gpu,&p);return p.limits.maxImageDimension2D;}\n    std::uint64_t presents{};')
s=replace(s,'void render(Scene &s, bool upload_in = true, bool readback_out = true)',
    'void render_base(Scene &s, bool upload_in = true, bool readback_out = true)')
start=s.index('    bool current(');end=s.index('    // Lazy residency',start)
s=s[:start]+'''    bool current(std::uint64_t key,std::uint64_t hash,unsigned w,unsigned h)const {
        return cache_current(key,hash,w,h)&&(!remaster_width()||(enhancement&&enhancement->cache_current(key,hash,w,h)));
    }
    #include "remaster_render.inc"
'''+s[end:]
s=replace(s,'VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};',
'''VkPhysicalDeviceFeatures features{},enabled{};f.vkGetPhysicalDeviceFeatures(gpu,&features);
        const unsigned af=remaster_af();if(af!=1&&af!=16)throw std::runtime_error("Unsupported remaster AF setting");
        if(af>1){VkPhysicalDeviceProperties properties{};f.vkGetPhysicalDeviceProperties(gpu,&properties);if(!features.samplerAnisotropy||properties.limits.maxSamplerAnisotropy<float(af))throw std::runtime_error("GPU cannot provide requested anisotropic filtering");enabled.samplerAnisotropy=VK_TRUE;}
        VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};dci.pEnabledFeatures=&enabled;''')
s=replace(s,'VkSamplerCreateInfo si{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};',
    'VkSamplerCreateInfo si{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};')
# Set anisotropy after the original sampler filter assignments.
anchor='check(f.vkCreateSampler(device, &si, nullptr, &s), "create sampler");'
if anchor not in s:
    anchor=next(line.strip() for line in s.splitlines() if 'vkCreateSampler(device' in line)
s=replace(s,anchor,'if(remaster_af()>1){si.anisotropyEnable=VK_TRUE;si.maxAnisotropy=float(remaster_af());si.magFilter=si.minFilter=VK_FILTER_LINEAR;}\n        '+anchor)
p.write_text(s)

p=HOST/'remaster_render.inc';s=p.read_text()
s=replace(s,'void render(Scene&s){','void render(Scene&s,bool upload_in=true,bool readback_out=true){')
s=replace(s,'if(!ow){render_base(s);return;}','if(!ow){render_base(s,upload_in,readback_out);return;}')
p.write_text(s)

p=HOST/'vdd.inc';s=p.read_text()
# Enhanced rendering retains exact guest-sized readback; latest lazy residency
# remains available unchanged for original-resolution execution.
s=replace(s,'static bool lazy_rt(){','static bool lazy_rt(){if(mw34::vkscene::Renderer::remaster_width())return false;')
old=(ASSET/'vdd.inc').read_text()
s=replace(s,'const unsigned g=host.vsurface_next;\n if(std::uint64_t(g)+n>vsurface_arena_end)deny("Virtual surface arena exhausted",g);',
'''if(host.vsurface_next<0x80000000U&&std::uint64_t(host.vsurface_next)+n>vsurface_arena_end){if(!std::getenv("MW34_REMASTER_BANKS"))deny("Virtual surface arena exhausted",host.vsurface_next);host.vsurface_next=0x80000000U;}
 const unsigned g=host.vsurface_next;const std::uint64_t limit=g>=0x80000000U?0xf0000000ULL:vsurface_arena_end;
 if(std::uint64_t(g)+n>limit)deny("Virtual surface arena exhausted",g);''')
begin=old.index('if(v.bpp==16&&!gdi_only)');end=old.index(' if(!shown){RECT rc',begin)
first=s.index('if(v.bpp==16&&!gdi_only)');last=s.index(' if(!shown){RECT rc',first)
s=s[:first]+old[begin:end]+s[last:]
p.write_text(s)

definition=OUT/'build-definition';definition.mkdir()
s=(CURRENT/'native/CMakeLists.txt').read_text()
s=replace(s,'get_filename_component(MW34_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)',
    'set(MW34_ROOT "'+ROOT.as_posix()+'")')
(definition/'CMakeLists.txt').write_text(s)
cache=(ROOT/'build/m4-crt-heap-carry-O2-lazy/CMakeCache.txt').read_text()
line=next(x for x in cache.splitlines() if x.startswith('MW34_MFC_OBJECT_LIST:'))
objects=Path(line.split('=',1)[1]);shutil.copy2(objects,OUT/'optimized-mfc-objects.txt')
(OUT/'source-snapshot.json').write_text(json.dumps({'origin':'Current optimized native host, with Remaster presentation/bank/model adapters','source_sha256':pins,'optimized_object_list_source':str(objects),'optimized_object_list_sha256':hashlib.sha256(objects.read_bytes()).hexdigest(),'enhanced_lazy_residency':False},indent=2)+'\n')
print('Prepared optimized native Remaster source snapshot:',OUT)
