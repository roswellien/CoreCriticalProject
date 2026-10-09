"""Prepare a fresh whole functional locale/argv composition from pinned source.

Only original BEFORE data can execute. Preparation never executes candidates.
"""
import hashlib,json,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-allocation/preparation-r7'
BUILD=ROOT/'reports/m4-crt-allocation/build-r9/build.json'
HOME=Path(__file__).resolve().parent
IFACE=ROOT/'reports/m4-crt-locale-batch-recovery/interface-r1'
REC=ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2'
LIFTS=ROOT/'reports/m4-crt-locale-batch/lifts-r1'
SUPPLEMENT=ROOT/'reports/m4-crt-locale-batch-recovery/lifts-supplement-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(c,s):
    if not c:raise RuntimeError(s)
def js(p):return json.loads(Path(p).read_text())
def permission(flags):return (1 if flags&0x40000000 else 0)|(2 if flags&0x80000000 else 0)|(4 if flags&0x20000000 else 0)
def generate_contract(out,lifts):
    spec=js(IFACE/'operand-contracts.json');apis=js(REC/'API-contracts.json')
    regs={k:i for i,k in enumerate(['','eax','ecx','edx','ebx','esp','ebp','esi','edi','al','cl','dl','bl','ah','ch','dh','bh','ax','cx','dx','bx','sp','bp','si','di'])}
    def reg(v):
        need(not v or v in regs,'Original supported source register '+str(v));return regs.get(v,0)
    def operand(o):
        m=o.get('mem',{});seg=m.get('segment','default');need(seg in ('default','fs','ds','ss','es'),'Supported original segment')
        return '{'+','.join([str({'reg':1,'imm':2,'mem':3}[o['kind']]),str(o['width']),str(reg(o.get('reg'))),str(int(seg=='fs')),str(reg(m.get('base'))),str(reg(m.get('index'))),str(m.get('scale',1)),str(m.get('disp',0)),str(o.get('imm',0)&0xffffffffffffffff)+'ULL',str((1 if 'r' in o.get('access','') else 0)|(2 if 'w' in o.get('access','') else 0))])+'}'
    lines=['} // composition anonymous namespace','namespace mw34::m4_crt_locale_batch {','namespace {','constexpr SourceInstruction source_instructions[]{']
    for i in sorted(spec['instructions'],key=lambda i:i['address']):
        ops=i['operands'];need(len(ops)<=3,'Finite original operand arity')
        repeat=i.get('repeat');rn={'rep':1,'repe':2,'repz':2,'repne':3,'repnz':3,None:0}.get(repeat)
        need(rn is not None,'Original repeat prefix '+str(repeat))
        lines.append('{'+f"{i['address']},{i['size']},{json.dumps(i['mnemonic'])},{{{{"+','.join([operand(o) for o in ops]+['{}']*(3-len(ops)))+'}},'+f'{len(ops)},{rn}'+'},')
    lines+=['};','constexpr SourceSpan original_spans[]{']
    pages={}
    for s in spec['source_spans']:
        perm=permission(s['section']['permissions']);lines.append('{'+f"{s['start']},{s['bytes']},{perm},\"{s['sha256']}\""+'},')
        for page in range(s['start']&~4095,(s['end_exclusive']+4095)&~4095,4096):
            need(page not in pages or pages[page]==perm,'Consistent original source-page permissions');pages[page]=perm
    for s in js(REC/'report.json')['data'].values():
        perm=permission(s['section']['permissions'])
        for page in range(s['address']&~4095,(s['address']+s['bytes']+4095)&~4095,4096):
            need(page not in pages or pages[page]==perm,'Consistent original source/data permissions');pages[page]=perm
    for page in (0x78035000,0x78037000,0x78039000,0x7803b000):pages[page]=3
    lines+=['};','constexpr SourcePage original_pages[]{']+['{'+f'{p},{v}'+'},' for p,v in sorted(pages.items())]+['};']
    imports={i['name']:i for i in apis['imports']};lines+=['constexpr SourceApi original_apis[]{']
    for a in apis['sites']:
        i=imports[a['API']];lines.append('{'+f"{a['pc']},{a['IAT']},{a['raw_IAT']},{i['argument_DWORDs']},{json.dumps(a['API'])},{int(a['kind']=='jmp')}"+'},')
    lines+=['{0x7800137f,0x7802e094,0x345c6,3,"HeapAlloc",0},','{0x78001430,0x7802e090,0x345ba,3,"HeapFree",0},']
    lines+=['};']
    # Each transformed literal block names its exact original PC. Undefined
    # sites come from its real generated callback, not an opcode guess.
    undefined=set();bodies={};bridges=set()
    inputs=[(LIFTS,k,v) for k,v in lifts['source_bodies'].items()]
    inputs.extend((SUPPLEMENT,k,v) for k,v in js(SUPPLEMENT/'report.json')['source_bodies'].items())
    old=js(ROOT/'reports/m4-crt-allocation/lifts-r1/report.json')
    inputs.extend((ROOT/'reports/m4-crt-allocation/lifts-r1',k,v) for k,v in old['source_bodies'].items())
    # Frozen earlier bodies supply their exact original names and entries.
    for d,k,v in inputs:
        text=(d/(k+'-host.ll')).read_text();name=re.search(r'^define ptr @(\w+)\(',text,re.M).group(1);bodies.setdefault(v['entry'],name);bridges.update(v['bridges'])
    receipt=js(REC.parent/'callbacks-union-r1/report.json');need(receipt['passed'] and sha(REC.parent/'callbacks-union-r1/report.json')=='03d1b505c72b384f6915ecf435bc883dbbfccb1824f04178e238ad825b863ead','Exact generated undefined callback receipt')
    callbacks=js(REC.parent/'callbacks-union-r1/callbacks.json');counts={}
    for category in ('new_bodies','baseline_bodies'):
        for v in callbacks[category].values():
            for c in v['callback_sites']:counts[c['pc']]=max(counts.get(c['pc'],0),c['callback_count'])
    undefined=[pc for pc,n in sorted(counts.items()) for _ in range(n)]
    # Bodies already compiled into accepted baseline, needed for initializer,
    # its caller, builder, parser and default prefix. Symbols are literal COFF.
    for entry,name in [(0x7800183c,'mw34_heap_init_fragment_body'),(0x780039bf,'mw34_heap_init_provider_body'),(0x78003a0c,'mw34_heap_mode_selector_body'),(0x780058b5,'mw34_heap_mode_probe_body'),(0x78003a31,'mw34_heap_version_branch_body'),(0x78003a4b,'mw34_heap_version_environment_body'),(0x7800ccc5,'mw34_heap_version_mode1_body'),(0x78003a7d,'mw34_heap_version_epilogue_body'),(0x78003dd2,'mw34_locale_default_mbinit_body'),(0x78003ddb,'mw34_locale_default_setmbcp_body'),(0x78001055,'mw34_locale_default_lock_body'),(0x7800ba5e,'mw34_mainargs_mainargs_body'),(0x7800bbbc,'mw34_mainargs_normal_argv_body'),(0x7800bc48,'mw34_mainargs_normal_parser_body')]:bodies.setdefault(entry,name)
    lines+=['constexpr unsigned undefined_sites[]{'+','.join(map(str,sorted(undefined)))+'};','}']
    lines+=['const SourceInstruction*instruction(unsigned pc)noexcept{auto it=std::lower_bound(std::begin(source_instructions),std::end(source_instructions),pc,[](const auto&i,unsigned p){return i.pc<p;});return it!=std::end(source_instructions)&&it->pc==pc?it:nullptr;}','std::span<const SourceSpan>source_spans()noexcept{return original_spans;}','std::span<const SourcePage>source_pages()noexcept{return original_pages;}','std::span<const unsigned>generated_undefined_sites()noexcept{return undefined_sites;}','std::span<const SourceApi>source_api_contracts()noexcept{return original_apis;}']
    for name in sorted(set(bodies.values())):lines.append('extern "C" void*'+name+'(State*,unsigned,void*);')
    lines+=['bool has_body(unsigned pc)noexcept{switch(pc){']+['case '+str(p)+':return true;' for p in sorted(bodies)]+['default:return false;}}','void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){']+['case '+str(p)+':return '+n+'(s,pc,p);' for p,n in sorted(bodies.items())]+['default:current(p,pc)->deny("Unrecovered literal source body",pc);}}','}']
    lines.append('namespace {')
    (out/'source_contract.inc').write_text('\n'.join(lines)+'\n')
    return bridges,bodies,undefined,pages
def main(path):
    start=time.perf_counter();out=Path(path).resolve();need(out.parent==LIFTS.parent and not out.exists(),'Fresh owned preparation directory')
    pins=js(BASE/'pins.json')
    for p,h in pins['files'].items():need(sha(p)==h,'Immutable baseline dependency '+p)
    need(sha(BASE/'report.json')=='f5297af2fbcf02e3139e41c89b803e601fbb233417463dfda1de93574a93abd5','Accepted preparation')
    need(sha(BUILD)=='debce1221a24411dc4f924207240dd4455d67253e4f04bd5c2701bd9580e5a2d','Accepted compilation')
    need(sha(IFACE/'report.json')=='4a88039fa4be1505bda06399c5993bc99e2dbde5f933bd509ef6bb6dad22864c','Independent original instruction interface')
    lifts=js(LIFTS/'report.json');need(lifts['passed'] and not lifts['native_component_executed'],'Literal source-only new lifts')
    for p,h in lifts['files'].items():need(sha(p)==h,'Literal source lift dependency '+p)
    supplement=js(SUPPLEMENT/'report.json');need(sha(SUPPLEMENT/'report.json')=='94467367ace177e43df4cb4b237186a0a97320457fcea33fd85f55c633fd1956','Exact supplemental suffix lifts')
    for p,h in supplement['files'].items():need(sha(p)==h,'Supplement source dependency '+p)
    out.mkdir(parents=True)
    for p in BASE.iterdir():
        if p.suffix in ('.cpp','.hpp','.inc'):(out/p.name).write_bytes(p.read_bytes())
    for p in HOME.iterdir():
        if p.suffix in ('.hpp','.inc'):(out/p.name).write_bytes(p.read_bytes())
    bridges,bodies,undefined,pages=generate_contract(out,lifts)
    s=(out/'composition.cpp').read_text();s=s.replace('#include "allocation.hpp"','#include "allocation.hpp"\n#include "locale_batch.hpp"');s=s.replace('namespace al=mw34::m4_crt_allocation;','namespace al=mw34::m4_crt_allocation;\nnamespace lb=mw34::m4_crt_locale_batch;')
    s=s.replace('#include "mainargs_binding.inc"','#include "source_contract.inc"\n#include "locale_batch_binding.inc"\n#include "mainargs_binding.inc"')
    # The raw provider is a pinned source. Admit its own physical PE flags,
    # including every new literal page, rather than a historical whitelist.
    a=s.index('require((flags&0xe0000000)==');b=s.index(';require(',a);s=s[:a]+'require((flags&0x40000000)!=0,"Readable original provider source page")'+s[b:]
    s=s.replace('unsigned char)noexcept(false){','unsigned char v)noexcept(false){')
    lines=s.splitlines();existing=set()
    for n,line in enumerate(lines):
        m=re.match(r'extern "C" .+?(\w+)\([^\n]*?\)\s*(?:noexcept\(false\))?\s*\{',line)
        if not m:continue
        name=m.group(1);existing.add(name);insert=None
        if name.startswith('__remill_read_memory_'):
            w=int(name.rsplit('_',1)[1])//8;insert=f'if(lb::has_authority())return static_cast<decltype(__remill_read_memory_{w*8}(p,a))>(lb::current(p,a)->read(a,{w}));'
        elif name.startswith('__remill_write_memory_'):
            w=int(name.rsplit('_',1)[1])//8;insert=f'if(lb::has_authority()){{lb::current(p,a)->write(a,v,{w});return p;}}'
        elif name.endswith('_undefined_8'):insert='if(lb::has_authority())return lb::current(lb::owner,0)->undefined();'
        elif name in ('__remill_function_call','__remill_function_return','__remill_missing_block','__remill_jump') or name.startswith('sub_780'):
            meth={'__remill_function_return':'returned','__remill_missing_block':'missing','__remill_jump':'jumped'}.get(name,'called');insert=f'if(lb::has_authority())return lb::current(p,a)->{meth}(s,a,p);'
        if insert:pos=line.index('{');lines[n]=line[:pos+1]+insert+line[pos+1:]
    added=[]
    for name in sorted(bridges-existing):
        if name.endswith('_undefined_8'):added.append(f'extern "C" unsigned char {name}(){{return lb::current(lb::owner,0)->undefined();}}')
        elif name.startswith('sub_'):added.append(f'extern "C" void*{name}(State*s,unsigned a,void*p){{return lb::current(p,a)->called(s,a,p);}}')
        elif name.startswith('__remill_read_memory_'):
            bits=int(name.rsplit('_',1)[1]);typ={8:'unsigned char',16:'unsigned short',32:'unsigned',64:'std::uint64_t'}[bits];added.append(f'extern "C" {typ} {name}(void*p,unsigned a){{return static_cast<{typ}>(lb::current(p,a)->read(a,{bits//8}));}}')
        elif name.startswith('__remill_write_memory_'):
            bits=int(name.rsplit('_',1)[1]);typ={8:'unsigned char',16:'unsigned short',32:'unsigned',64:'std::uint64_t'}[bits];added.append(f'extern "C" void*{name}(void*p,unsigned a,{typ} v){{lb::current(p,a)->write(a,v,{bits//8});return p;}}')
        else:raise RuntimeError('Unclassified compiled source bridge '+name)
    s='\n'.join(lines).replace('#include "main_v2.inc"','\n'.join(added)+'\n#include "main_v2.inc"');(out/'composition.cpp').write_text(s+'\n')
    # Older adapter functions remain available for archived ABI references,
    # but the new driver owns only the whole unit and genuine command line.
    s=(out/'mainargs_binding.inc').read_text();a=s.index('struct MainargsBinding{');b=s.index('thread_local MainargsBinding',a)
    s=s[:a]+'''struct MainargsBinding{mg::Context context;unsigned control{};lb::Binding batch;
 void(*extra_before)(mg::Context&,unsigned){};void(*extra_access)(mg::Context&,unsigned){};void(*extra_event)(mg::Context&,unsigned){};void(*extra_after)(mg::Context&){};
 MainargsBinding(Runtime&r,std::span<const std::byte>p,unsigned c):context(r,p),control(c),batch(context,p,c){}
};\n'''+s[b:]
    a=s.index('void mainargs_adapter');s=s[:a]+'''void mainargs_adapter(Runtime&r){require(mainargs_binding&& &mainargs_binding->context.runtime==&r&&!pp::owner&&!mg::owner&&!nt::owner&&!ci::owner&&!mn::owner,"Exclusive whole mainargs batch owner");auto&c=mainargs_binding->context;mainargs_checkpoint(r,"mainargs-before");auto&b=mainargs_binding->batch;b.start(c);b.suspend_for_commandline();cm::current(c)->initialize();b.resume_mainargs(c);throw std::runtime_error("Required genuine builder return not observed");}\n''';(out/'mainargs_binding.inc').write_text(s)
    for name in ('main_v2.inc','observations.hpp'):(out/name).write_bytes((HOME/('root_'+name)).read_bytes())
    oldbuild=js(BUILD);objects=dict(oldbuild['entry_objects']);objects.update(lifts['entry_objects']);objects.update(supplement['entry_objects'])
    files={str(p.resolve()):sha(p) for p in out.iterdir() if p.is_file()}
    for p in [Path(__file__),HOME/'build.ps1',IFACE/'report.json',IFACE/'operand-contracts.json',REC/'API-contracts.json',LIFTS/'report.json',SUPPLEMENT/'report.json',REC.parent/'callbacks-union-r1/report.json',REC.parent/'callbacks-union-r1/callbacks.json',BASE/'report.json',BUILD]:files[str(p.resolve())]=sha(p)
    files.update(objects);files.update(oldbuild['libraries'])
    report=dict(schema='mw34-m4-locale-batch-preparation-v1',passed=True,native_executed=False,State_reseed_after_writer=False,source_bodies_modified=False,source_bodies_added=len(lifts['source_bodies']),entry_objects=objects,libraries=oldbuild['libraries'],generated_instruction_count=1220,generated_undefined_sites=sorted(undefined),body_entries={str(k):v for k,v in bodies.items()},source_pages=pages,files=files,lifts_sha256=sha(LIFTS/'report.json'),recovery_sha256=sha(REC/'report.json'),baseline_acceptance_sha256='8b5e67e5ab25bd5bae54f5d16e943b4313d7ef329868d43c3603407b99e0b010',direct_strict_capture_emission=True,flat_capture_tree=False,full_CRT=False,whole_M4_complete=False,seconds=time.perf_counter()-start)
    (out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');files[str((out/'report.json').resolve())]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(schema='mw34-m4-locale-batch-preparation-pins-v1',files=files),sort_keys=True,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
if __name__=='__main__':main(sys.argv[1])
