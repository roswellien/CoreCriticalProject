"""Compose a private lighting candidate from the current main native host.

Inputs are local host trees, not distributable game artifacts. Pin the reviewed
main/baseline/lighting adapter versions before using three-way reconciliation;
never replace the current playable host or its profile. Existing native object
lists are retained, with no terrain projection bypass or retranslation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile

from apply_material_normals import apply as material_normals
from apply_perf_env_cache import apply_model_cache
from apply_menu_wave import apply as menu_wave
from apply_sun_camera_binding import apply as sun_camera_binding

FILES=('vk_scene.hpp','mfc_stage.hpp','d3d_provider.inc','mesh_override_stage.inc','vdd.inc','widescreen_stage.inc')
CONFLICT=re.compile(r'^<<<<<<<[^\n]*\n(.*?)^=======\n(.*?)^>>>>>>>[^\n]*\n',re.M|re.S)
LIGHTING_BODY=''' #include "world_direct_stage.inc"
 #include "sun_lighting_stage.inc"
 #include "sun_tl_capture_stage.inc"
 #include "divergence_trace_stage.inc"
 void*lighting_body(State*s,unsigned target,void*p,Body body){
  if(world_enabled()&&target==0x4f6720){++world_cell_depth;try{void*r=remaster_body_inner(s,target,p,body);--world_cell_depth;return r;}catch(...){--world_cell_depth;throw;}}
  if(world_enabled()&&target==0x53f2e0){auto previous=world_scope;world_scope=world_begin(state.gpr.rcx.dword,state.gpr.rsp.dword-4);try{void*r=remaster_body_inner(s,target,p,body);world_scope=std::move(previous);return r;}catch(...){world_scope=std::move(previous);throw;}}
  return remaster_body_inner(s,target,p,body);
 }
'''


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def compose(main,baseline,lighting,output):
    pins=json.loads(Path(__file__).with_name('normal_mapping_source_pins.json').read_text())
    for key,folder in [('main',main),('baseline',baseline),('lighting',lighting)]:
        for name,expected in pins[key].items():
            if digest(folder/'host-source'/name)!=expected:
                raise ValueError('Unreviewed '+key+' adapter version: '+name)
    if output.exists():raise ValueError('Choose a new candidate directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='normal-integration-',dir=output.parent) as temporary:
        work=Path(temporary);candidate=work/'candidate';candidate.mkdir()
        shutil.copytree(main/'host-source',candidate/'host-source')
        for name in ['build-definition','build.ps1','optimized-mfc-objects.txt']:
            source=main/name
            if source.is_dir():shutil.copytree(source,candidate/name)
            else:shutil.copyfile(source,candidate/name)
        host=candidate/'host-source'
        expected_counts={'mfc_stage.hpp':2,'d3d_provider.inc':2,'mesh_override_stage.inc':5,'vdd.inc':1,'widescreen_stage.inc':0}
        for name in FILES:
            if name=='vk_scene.hpp':
                # Main's capture methods are required by photo/replay. The rest
                # of its renderer predates retained-world and lighting support.
                text=(main/'host-source'/name).read_text()
                methods=text[text.index('    void capture_fullres_rgb('):text.index('    // Enhanced settings are explicit;')]
                lit=(lighting/'host-source'/name).read_text()
                (host/name).write_text(lit.replace('    // Enhanced settings are explicit;',methods+'    // Enhanced settings are explicit;'))
                continue
            paths=[]
            for key,folder in [('main',main),('baseline',baseline),('lighting',lighting)]:
                path=work/(key+'-'+name);path.write_bytes((folder/'host-source'/name).read_text().encode());paths.append(str(path))
            merged=subprocess.run(['git','merge-file','-p',*paths],capture_output=True)
            if merged.returncode!=expected_counts[name]:raise ValueError('Unexpected integration conflict set: '+name)
            text=merged.stdout.decode();count=0
            def resolve(match):
                nonlocal count
                index=count;count+=1;ours,theirs=match[1],match[2]
                if name=='vdd.inc':return ours
                if name=='mfc_stage.hpp':
                    if index==0:return LIGHTING_BODY
                    return ours.replace('return remaster_body_inner(s,target,p,body);});});','return lighting_body(s,target,p,body);});});')
                if name=='d3d_provider.inc' and index==0:
                    return theirs.replace('if(!override_suppress_draw())','if(!override_suppress_draw()&&!photo_replay_suppress_d3d_draw())')
                return theirs
            text=CONFLICT.sub(resolve,text)
            if count!=expected_counts[name] or '<<<<<<<' in text:raise ValueError('Unresolved integration conflict: '+name)
            if name=='mfc_stage.hpp':
                text=text.replace('  if(target==0x545720)return terrain_545720_probe(s,target,p,body);\n','')
                text=text.replace('hooked_?remaster_body(s,target,p,body):body(s,target,p)','remaster_body(s,target,p,body)')
                text=text.replace(' #include "mesh_override_stage.inc"',' mw34::GeometryProfile geometry_profile;\n #include "mesh_override_stage.inc"')
            if name=='vdd.inc':
                anchor=' if(host.frame_dump&&(host.frames==1||host.frames%host.frame_dump==0))'
                if text.count(anchor)!=1:raise ValueError('Frame diagnostics anchor changed')
                text=text.replace(anchor,' world_present();geometry_profile.present(host.frames);\n'+anchor)
            (host/name).write_text(text)
        for name in ['sun_lighting.hpp','sun_lighting_stage.inc','sun_tl_capture_stage.inc','sun_world_vert.h','sun_model_vert.h','sun_scene_frag.h','sun_tl_vert.h','sun_shadow_vert.h','geometry_profile.hpp','world_binding.hpp','world_fast_binding.hpp','world_geometry_stage.inc','world_direct_stage.inc','world_scene_vert.h','divergence_trace_stage.inc']:
            if (host/name).exists():raise ValueError('Unexpected main lighting dependency: '+name)
            shutil.copyfile(lighting/'host-source'/name,host/name)
        material_normals(host);apply_model_cache(host);menu_wave(host);sun_camera_binding(host)
        for name in ['heap_partitions.hpp','photo_replay_stage.inc','photo_replay_math.hpp','turret_aim_stage.inc','turret_aim_math.hpp','guest_memory_cached.cpp']:
            if digest(host/name)!=digest(main/'host-source'/name):raise ValueError('Changed protected main service: '+name)
        from apply_capture_readback import apply as apply_capture_readback
        apply_capture_readback(host)
        (candidate/'integration-inputs.json').write_text(json.dumps(pins,indent=2))
        candidate.rename(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['main','baseline','lighting','output']:parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    compose(args.main.resolve(strict=True),args.baseline.resolve(strict=True),args.lighting.resolve(strict=True),args.output.resolve())
