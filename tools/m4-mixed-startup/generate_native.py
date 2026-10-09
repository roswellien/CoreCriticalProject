"""Fresh mixed-runtime derivatives; frozen standalone gates stay immutable."""
from pathlib import Path
import hashlib,json,re,sys

ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p):return p.read_text(encoding='utf-8-sig')
def includes(source,origin):
    def sub(m):
        name=m[1]
        if name=='probe_spec.hpp':p=ROOT/'reports/m4-fp-startup/research-r1/probe_spec.hpp'
        elif name=='memory/guest_memory.hpp':return m[0]
        else:p=origin.parent/name
        if not p.is_file():raise ValueError(f'Missing literal dependency {p}')
        return '#include "'+p.as_posix()+'"'
    return re.sub(r'#include "([^"]+)"',sub,source)
def rename(source,prefix):
    symbols=set(re.findall(r'\b(?:__remill_\w+|mw34_(?:actual_\w+|fp_store_exception_test|\w+_primitive_admit))\b',source))
    mapping={s:prefix+'_'+s for s in symbols}
    for old,new in sorted(mapping.items(),key=lambda pair:-len(pair[0])):source=re.sub(r'\b'+re.escape(old)+r'\b',new,source)
    return source,mapping
def once(source,old,new):
    if source.count(old)!=1:raise ValueError(f'Expected one derivative anchor: {old}')
    return source.replace(old,new)

COMPONENTS={
 'first':('m4-fp-native/native_first.cpp','m4-fp-native', ['m4-fp-store-repair/store_test.cpp'],['m4-fp-store-repair/accumulated-r1/verified.ll'],[0x4133c0]),
 'simple':('m4-fp-simple-batch/native_batch.cpp','m4-fp-simple-batch',['m4-fp-simple-batch/store_test.cpp'],['m4-fp-simple-batch/repaired-r2/verified.ll'],[0x4b5af0,0x4c79d0]),
 'sqrt':('m4-fp-sqrt/native_sqrt.cpp','m4-fp-sqrt',['m4-fp-sqrt/raw80.cpp','m4-fp-sqrt/store_test.cpp'],['m4-fp-sqrt/repaired-r2/verified.ll'],[0x4adb50]),
 'cosine':('m4-fp-transcendental/native_cosine.cpp','m4-fp-transcendental',['m4-fp-cosine-repair/raw80_status.cpp','m4-fp-store-repair/store_test.cpp'],[f'm4-fp-transcendental/cosine-repaired-r1/{x}-verified.ll' for x in ['4ce5a0','4ce5c0','4ce5e0','4ce600']],[0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600]),
 'sincos':('m4-fp-trigonometric/native_sincos.cpp','m4-fp-trigonometric',['m4-fp-trigonometric/sincos_raw80.cpp','m4-fp-trigonometric/sincos_store_test.cpp'],['m4-fp-trigonometric/sincos-repaired-r1/verified.ll'],[0x4c78f0]),
 'atan':('m4-fp-trigonometric/native_atan.cpp','m4-fp-trigonometric',['m4-fp-trigonometric/atan_raw80.cpp','m4-fp-trigonometric/atan_store_test.cpp'],['m4-fp-trigonometric/atan-repaired-r2/verified.ll'],[0x4b7020]),
}

def main(out):
    out=Path(out).absolute();out.relative_to(ROOT/'reports/m4-mixed-startup')
    out.mkdir(exist_ok=False,parents=True)
    original={};generated={};configuration=[]
    for name,(cpp,folder,bridges,irs,entries) in COMPONENTS.items():
        source=ROOT/'tools'/cpp;original[str(source)]=sha(source)
        s=text(source);s=s[:s.index('int main(int argc,char **argv)')]
        ns=re.search(r'namespace (mw34::\w+) \{',s)[1]
        s=includes(s,source)
        old=re.search(r'constexpr std::uint32_t ([^;]*frame=0x20001800,sentinel=0x10000100);',s)
        if not old:raise ValueError('Missing exact standalone frame domain')
        prefix=old[1].split('frame=')[0]
        s=s[:old.start()]+(('constexpr std::uint32_t '+prefix.rstrip(',')+';\n') if prefix else '')+'static thread_local std::uint32_t frame{},sentinel{};'+s[old.end():]
        s=s.replace('constexpr std::array<Event,4> sequence','const std::array<Event,4> sequence')
        s,mapping=rename(s,'mw34_mixed_'+name)
        setup=''
        if name=='simple':setup='entry=runtime.cpu().eip;'
        if name=='cosine':
            construct='Root root{};bool found{};for(auto r:mw34::m4_fp_cosine::roots)if(r.entry==runtime.cpu().eip){root=r;found=true;}require(found,"Missing cosine route");Context context(runtime.memory(),root);'
        else:construct='Context context(runtime.memory());'
        count='r.primitives=context.primitives;' if name in ['sqrt','cosine','sincos','atan'] else ''
        wrapper=f'''
#include "{(ROOT/'tools/m4-mixed-startup/native_protocol.hpp').as_posix()}"
namespace mw34::m4_mixed {{
void {name}(m4_runtime::Runtime &runtime){{
 using namespace {ns};
 require(runtime.domain()==m4_runtime::Domain::admitted_game&&runtime.remill_seeded(),"Shared FP requires admitted persistent State");
 auto &state=*std::launder(reinterpret_cast<State *>(runtime.remill_state().data()));
 require(state.addr.ds_base.dword==0&&state.addr.ss_base.dword==0&&state.addr.fs_base.dword==runtime.fs_base().value,"Unsupported shared FP segment bases");
 {ns}::frame=runtime.cpu().esp;{ns}::sentinel=runtime.memory().load<std::uint32_t>({{{ns}::frame}});{setup}
 m4_mixed::overlay_cpu(state,runtime.cpu());
 validate_fp(runtime,state);
 snapshot(runtime,state,true);{construct}
 Result result{{}};result.cw=state.x87.fxsave.cwd.flat;
 {{FpuScope isolation(static_cast<std::uint16_t>(result.cw));context.enter(state);
   require(!context.failed&&context.complete&&isolation.restored(result),"Mixed FP context or host restoration failed");
   m4_mixed::host(result.host_before.data(),result.host_after.data(),result.host_env_before.data(),result.host_env_after.data());}}
 snapshot(runtime,state,false);auto &r=*observation;
 events(context.events,context.event_count);r.reads=context.reads;r.writes=context.writes;r.clears=context.clears;r.tests=context.tests;r.returns=context.returns;{count}
 r.state_seeded=runtime.remill_seeded();
 const auto c=m4_mixed::cpu(state);runtime.cpu()={{c.gpr[0],c.gpr[1],c.gpr[2],c.gpr[3],c.gpr[4],c.gpr[5],c.gpr[6],c.gpr[7],c.flags,c.pc}};
 sync_fx(runtime,state);
}}
}}
'''
        s='#include <algorithm>\n#include <memory>\n'+s+wrapper
        dest=out/(name+'.cpp');dest.write_text(s,encoding='utf-8');generated[str(dest)]=sha(dest)
        allsymbols=dict(mapping);parts=[]
        for i,b in enumerate(bridges):
            p=ROOT/'tools'/b;original[str(p)]=sha(p)
            content,m=rename(text(p),'mw34_mixed_'+name);allsymbols.update(m)
            dest=out/f'{name}-bridge-{i}.cpp';dest.write_text(content,encoding='utf-8');generated[str(dest)]=sha(dest);parts.append(str(dest))
        modules=[]
        for i,ir in enumerate(irs):
            p=ROOT/'reports'/ir;original[str(p)]=sha(p);content=text(p)
            for old,new in allsymbols.items():content=re.sub(r'@'+re.escape(old)+r'\b','@'+new,content)
            # Preserve every instruction/type/value apart from external bridge names.
            reverse=content
            for old,new in allsymbols.items():reverse=re.sub(r'@'+re.escape(new)+r'\b','@'+old,reverse)
            if reverse!=text(p):raise ValueError('Bridge namespace change was not reversible')
            dest=out/f'{name}-{i}.ll';dest.write_text(content,encoding='utf-8');generated[str(dest)]=sha(dest);modules.append(str(dest))
        configuration.append(dict(name=name,cpp=str(out/(name+'.cpp')),bridges=parts,modules=modules,entries=entries,mapping=allsymbols))
    for name,folder in [('chain','m4-initializer-chain'),('integer','m4-integer-startup')]:
        directory=out/name;directory.mkdir()
        p=ROOT/'tools'/folder/'execution.hpp';original[str(p)]=sha(p)
        s=includes(text(p),p)
        s=once(s,'// Reserved FX bytes and capability mask are not architectural restoration observations.','mw34::m4_mixed::host(saved.bytes,after.bytes,legacy_env,env_after);\n        // Reserved FX bytes and capability mask are not architectural restoration observations.')
        s='#include "'+(ROOT/'tools/m4-mixed-startup/native_protocol.hpp').as_posix()+'"\n'+s
        dest=directory/'execution.hpp';dest.write_text(s,encoding='utf-8');generated[str(dest)]=sha(dest)
        p=ROOT/'tools'/folder/'runtime_adapter.cpp';original[str(p)]=sha(p);s=text(p)
        s=s.replace('#include "runtime_adapter.hpp"','#include "'+(p.parent/'runtime_adapter.hpp').as_posix()+'"')
        s=once(s,'    {\n        FpuScope host;', '    mw34::m4_mixed::snapshot(runtime,s,true);\n    {\n        FpuScope host;')
        anchor='    const auto c=observed_cpu(s);'
        observation_code='''    mw34::m4_mixed::snapshot(runtime,s,false);
    auto &mixed=*mw34::m4_mixed::observation;
    mw34::m4_mixed::events(context.events,context.trace_count);mixed.route_count=context.route_count;mixed.state_seeded=runtime.remill_seeded();
    for(unsigned i=0;i<context.route_count;++i){const auto &source=context.routes[i];auto &route=mixed.routes[i];route.entry=source.entry_pc;route.ret=source.return_pc;route.complete=source.complete;std::memcpy(&route.before,&source.before,40);std::memcpy(&route.after,&source.after,40);}
    for(unsigned i=0;i<context.trace_count;++i){if(context.events[i].operation)++mixed.writes;else ++mixed.reads;}
'''
        observation_code+=('    mixed.returns=context.returns;for(unsigned i=0;i<context.route_count;++i)mixed.routes[i].pop=context.routes[i].pop_bytes;\n' if name=='chain' else '    mixed.returns=1;\n')
        s=once(s,anchor,observation_code+anchor)
        dest=directory/'runtime_adapter.cpp';dest.write_text(s,encoding='utf-8');generated[str(dest)]=sha(dest)
    report=dict(passed=True,scope='Fresh derived adapter/bridge namespaces and exact reversible static IR renaming only; no execution or equivalence claim',original_sources=original,generated_sources=generated,components=configuration)
    (out/'generation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,components=6,FP_roots=10,generated_files=len(generated))))
if __name__=='__main__':main(sys.argv[1])
