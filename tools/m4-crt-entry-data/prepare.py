"""Additive native FDIV-to-entry data composition; every ancestor stays frozen."""
import hashlib, json, pathlib, shutil, sys
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-entry-data'
def sha(p):
    with pathlib.Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def replace(s,a,b):
    assert s.count(a)==1, a
    return s.replace(a,b)
def main(out):
    out=pathlib.Path(out).resolve();assert out.parent==BASE and not out.exists()
    ancestor=ROOT/'reports/m4-crt-fdiv-entry-prefix/preparation-r2'
    receipt=json.loads((ancestor/'report.json').read_text())
    assert receipt['passed'] and receipt['State_bytes']==3504
    files={}
    for p,h in json.loads((ancestor/'pins.json').read_text())['files'].items():
        assert sha(p)==h,p;files[p]=h
    for p in (ancestor/'report.json',ancestor/'pins.json'):files[str(p)]=sha(p)
    s=(ancestor/'composition.cpp').read_text()
    s=replace(s,'extern "C" void *sub_5ac3a0(State*,unsigned,void*) noexcept(false);','extern "C" void *sub_5ac3a0(State*,unsigned,void*) noexcept(false);\nextern "C" void *sub_5ac5c0(State*,unsigned,void*) noexcept(false);')
    start=s.index('  r.register_translation(');end=s.index('\n }',start)
    s=s[:end]+'''\n  r.register_translation({{0x5ac5c0},{Abi::Cdecl,0,true},&leaf_adapter,"Literal translated CRT RET leaf",{Domain::admitted_game,m4::admitted_image_hash,1,"ae3f4619b0413d70d3004b9131c3752153074e45725be13b9a148978895e359e",native_sha,"0c67cae86dad6468e082607ebe9d2b2504094829adb28e37b0c082d6e158d724"}});''' +s[end:]
    s=replace(s,' static void adapter(Runtime&r){',' static void leaf_adapter(Runtime&r){require(owner&& &owner->r_==&r,"Leaf owner absent");owner->guard();project(owner->s_,r.cpu());auto*p=sub_5ac5c0(&owner->s_,0x5ac5c0,owner);require(p==owner,"Literal leaf memory token returned");r.cpu()=cpu(owner->s_);}\n static void adapter(Runtime&r){')
    s=replace(s,'constexpr std::array<std::array<unsigned,3>,3>calls{{{0x5ac3cf,0x5bb5a4,0x5ac3d5},{0x5ac3ec,0x5bb57c,0x5ac3f2},{0x5ac3fa,0x5bb504,0x5ac400}}};','constexpr std::array<std::array<unsigned,3>,4>calls{{{0x5ac3cf,0x5bb5a4,0x5ac3d5},{0x5ac3ec,0x5bb57c,0x5ac3f2},{0x5ac3fa,0x5bb504,0x5ac400},{0x5ac428,0x5bb50c,0x5ac42e}}};')
    s=replace(s,'r_.call_direct({target},{w.value});throw std::runtime_error("Unreviewed helper unexpectedly returned");','r_.call_direct({target},{w.value});project(s_,r_.cpu());return this;')
    s=replace(s,' const auto&events()const{return events_;}', ' void*returned(State*s,unsigned pc){guard();require(s==&s_&&pc==0x5ac41a&&s_.gpr.rip.dword==pc,"Only actual translated RET leaf return admitted");return this;}\n const auto&events()const{return events_;}')
    s=replace(s,'extern "C" void*__remill_function_return(State*,unsigned,void*) noexcept(false) {throw std::runtime_error("Unreached required return bridge");}','extern "C" void*__remill_function_return(State*s,unsigned a,void*p) noexcept(false) {return static_cast<Context*>(p)->returned(s,a);}')
    s=replace(s,'s==&c->state()&&a==entry,"Only actual ordinary entry reached"','s==&c->state()&&(a==entry||a==0x5ac5c0),"Only actual ordinary entry or literal RET leaf reached"')
    s=replace(s,'#include "composition_main.inc"','#include "main.inc"')
    out.mkdir(parents=True)
    shutil.copyfile(ancestor/'composition.cpp',out/'composition-ancestor.cpp')
    shutil.copyfile(ancestor/'seed.hpp',out/'seed.hpp')
    helpers=(ROOT/'tools/m4-crt-fdiv-entry-prefix/composition_main.inc').read_text()
    helpers=helpers[:helpers.index('int main(int argc,char**argv)')]
    (out/'observations.hpp').write_text(helpers)
    (out/'composition.cpp').write_text(s)
    for p in (out/'composition.cpp',out/'composition-ancestor.cpp',out/'seed.hpp',out/'observations.hpp',ROOT/'tools/m4-crt-fdiv-entry-prefix/composition_main.inc',pathlib.Path(__file__).resolve()):files[str(p)]=sha(p)
    report=dict(passed=True,scope='Additive composition preparation; no execution or acceptance',
                source_sha256=sha(out/'composition.cpp'),parent_sha256=sha(ancestor/'composition.cpp'),
                State_bytes=3504,State_reseed_after_writer=False,entry_projection='Only outer ESP/EIP; three services and real RET leaf project CPU without touching FP or opaque State',
                data_source_PC=0x5ac408,data_consumer_PC=0x5ac40d,data_store_PC=0x5ac40f,
                actual_leaf=0x5ac5c0,next_missing_service_PC=0x5ac428,next_missing_service_IAT=0x5bb50c,
                game_IR_or_source_mutated=False,shared_r9_mutated=False,full_CRT=False,whole_M4_complete=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json')
    (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main(sys.argv[1])
