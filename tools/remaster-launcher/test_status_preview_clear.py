"""Exercise actual host clear classification/rectangle code over a depth occluder.

The fixture compiles the supplied host's authored functions, uses no game data,
and fails against the old raw surface depth-fill path. The near-depth control
models cockpit geometry covering the status display; the preview is farther
away and becomes visible only where its dedicated depth clear really ran.
"""
import argparse
from pathlib import Path
import subprocess


def definition(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    level = 1
    end = opening + 1
    while level:
        level += (source[end] == '{') - (source[end] == '}')
        end += 1
    if source[end:end + 1] == ';':
        end += 1
    return source[start:end]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    host = args.host.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    wide = (host / 'widescreen_stage.inc').read_text(encoding='utf-8')
    renderer = (host / 'vk_scene.hpp').read_text(encoding='utf-8')
    sun = (host / 'sun_lighting_stage.inc').read_text(encoding='utf-8')
    vdd = (host / 'vdd.inc').read_text(encoding='utf-8')
    fixed = 'fill(*v,status_preview_depth_rect(dst,v->width,v->height),load(fx+80)&0xffff);' in vdd
    helper = ((host / 'status_preview_clear_stage.inc').read_text(encoding='utf-8') if fixed else
              'RECT status_preview_depth_rect(RECT r,unsigned,unsigned){return r;}')
    source = r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <xmmintrin.h>
unsigned target_width=3440,target_height=1440;
namespace mw34::vkscene {
struct Renderer {
 static unsigned remaster_width(){return target_width;}
 static unsigned remaster_height(){return target_height;}
''' + definition(renderer, 'static bool widescreen()') + r'''
};
''' + definition(renderer, 'struct HostFpEnvironment') + r'''
}
struct Fixture {
 struct Host {unsigned frames=100;}host;
 bool enabled=true,frontend=false;
 unsigned wide_world_frame=100,wide_radar_mode=0,depth=0;
 std::array<unsigned,16>returns{};
 unsigned recorded_role{};RECT recorded_box{};
 void override_preview_record_rect(unsigned role,RECT box){recorded_role=role;recorded_box=box;}
 bool wide_on(){return enabled&&mw34::vkscene::Renderer::widescreen();}
 bool frontend_on(){return frontend;}
 bool target_marker_zoom(){return false;}
 float wide_zoom_border_anchor(){return 0;}
 [[noreturn]]void deny(const char*,unsigned){throw std::runtime_error("Unexpected scope");}
''' + definition(wide, 'enum WideHudRole') + '\n' + '\n'.join(
        definition(wide, signature) for signature in (
            'unsigned wide_hud_role()', 'float wide_hud_factor(', 'float wide_anchor(', 'RECT wide_rect(')
    ) + '\n' + definition(sun, 'struct SunCaptureFp') + '\n' + helper + r'''
};
unsigned checks=0;
void check(bool pass,const char* why){++checks;if(!pass)throw std::runtime_error(why);}
bool same(RECT a,RECT b){return a.left==b.left&&a.top==b.top&&a.right==b.right&&a.bottom==b.bottom;}
void occluder(unsigned width,unsigned height,unsigned producer,unsigned role,RECT original){
 target_width=width;target_height=height;
 Fixture fixture;fixture.depth=3;fixture.returns={0x401234,producer,0x5777ab};
 const bool classified=fixture.wide_hud_role()==(fixture.wide_on()?role:Fixture::WideWorld);
 const RECT expected=fixture.wide_rect(original,role,640,480);
 const unsigned csr=_mm_getcsr();_mm_setcsr(0x3fa0);
 const RECT cleared=fixture.status_preview_depth_rect(original,640,480);
 check(_mm_getcsr()==0x3fa0,"Status clear changed guest FP state");_mm_setcsr(csr);
 // A nearer cockpit surface was drawn first, with the engine's reversed Z.
 std::vector<float>depth(640*480,.9f);
 for(long y=cleared.top;y<cleared.bottom;++y)
  for(long x=cleared.left;x<cleared.right;++x)depth[y*640+x]=0;
 unsigned visible=0,hidden=0;
 for(long y=expected.top;y<expected.bottom;++y)
  for(long x=expected.left;x<expected.right;++x){
   const bool passes=.3f>=depth[y*640+x];visible+=passes;hidden+=!passes;
  }
 std::cout<<width<<'x'<<height<<" role="<<role<<" visible="<<visible<<" hidden="<<hidden<<'\n';
 check(hidden==0&&visible>0,"Cockpit depth cuts away part of the status mech");
 check(classified,"Status depth clear lacks its original producer role");
 check(same(cleared,expected),"Status clear does not follow the exact preview rectangle");
 check(depth[200*640+300]==.9f,"Unrelated world depth was cleared");
}
int main(){try{
 unsigned failures=0;
 for(auto size:{std::array<unsigned,2>{1920,1080},{2560,1440},{3440,1440},{1920,1440}}){
  try{occluder(size[0],size[1],0x43c748,Fixture::WideRight,{530,370,605,470});}
  catch(const std::exception& e){++failures;std::cerr<<"FAIL: "<<e.what()<<'\n';}
  try{occluder(size[0],size[1],0x43c72a,Fixture::WideLeft,{10,370,85,470});}
  catch(const std::exception& e){++failures;std::cerr<<"FAIL: "<<e.what()<<'\n';}
 }
 target_width=3440;target_height=1440;
 Fixture fixture;const RECT local{530,370,605,470},full{0,0,640,480};
 for(unsigned pc:{0x43c725,0x43c743,0x43c729,0x43c72b,0x43c747,0x43c749,0x441480,0x442a87}){
  fixture.depth=1;fixture.returns[0]=pc;
  check(same(fixture.status_preview_depth_rect(local,640,480),local),"Unknown depth fill was transformed");
 }
 fixture.returns[0]=0x43c72a;
 check(same(fixture.status_preview_depth_rect(full,640,480),full),"Full-target clear changed");
 fixture.enabled=false;
 check(same(fixture.status_preview_depth_rect(local,640,480),local),"Original-compatible clear changed");
 fixture.enabled=true;fixture.frontend=true;
 check(same(fixture.status_preview_depth_rect(local,640,480),local),"Frontend clear changed");
 check(failures==0,"Status depth-clear cases failed");
 std::cout<<"PASS "<<checks<<" status depth-clear/occluder checks\n";return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
'''
    if 'override_preview_record_rect' in helper:
        source = source.replace(
            'const RECT cleared=fixture.status_preview_depth_rect(original,640,480);',
            'const RECT cleared=fixture.status_preview_depth_rect(original,640,480);\n'
            ' check(fixture.recorded_role==role&&same(fixture.recorded_box,original),'
            '"Preview fit did not receive the original unadapted rectangle");')
    fixture = output / 'status-depth-checks.cpp'
    fixture.write_text(source, encoding='utf-8')
    compiler = Path('D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe')
    developer = Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/Tools/VsDevCmd.bat')
    exe = output / 'status-depth-checks.exe'
    script = output / 'build.cmd'
    script.write_text(f'@echo off\ncall "{developer}" -arch=x64 >nul\n"{compiler}" /nologo /std:c++20 /EHsc /O2 "{fixture}" /Fe:"{exe}" /Fo:"{output / "status-depth-checks.obj"}"\n', encoding='utf-8')
    build = subprocess.run(['cmd', '/c', str(script)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    (output / 'build.txt').write_text(build.stdout + build.stderr, encoding='utf-8')
    if build.returncode:
        raise RuntimeError(f'Fixture compilation failed; see {output / "build.txt"}')
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    (output / 'result.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
    print(result.stdout + result.stderr, end='')
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
