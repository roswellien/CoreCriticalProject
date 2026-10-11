"""Prepare nine current constructor refusal/poisoned-retry/cleanup cases.

This emits small source only. It never builds or launches a worker, reads a
capture, repairs a failed source machine, or invents a list/owner generation.
The mutation is applied at the actual measured constructor phase's own BEFORE.
"""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact additive controls hunk '+a[:100]);return s.replace(a,b,1)
def main(name):
    out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh code-only controls recipe');out.mkdir(parents=True);files={}
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Exact current controls source input');files[str(p)]=v;return p
    parent=pin(R/'reports/m4-constructor-native/fixture-preparation-r3/report.json','5507c72aef7bcf8afdd7c2b6fe3a906f3c65da58e69cc555f0671670cf289ad9');recipe=json.loads(parent.read_bytes());need(recipe['passed']and not recipe['native_executed'],'Current unexecuted positive fixture')
    # Inputs are only copied small compilation sources. Final builder must
    # rehash the inherited objects/libraries itself before ordinary execution.
    for p in parent.parent.rglob('*'):
        if p.is_file()and p.suffix.lower()in('.cpp','.hpp','.inc','.s','.json')and p.name!='report.json':
            q=out/p.relative_to(parent.parent);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(pin(p,recipe['files'][str(p.resolve())]).read_bytes())
    source=pin(parent.parent/'fixture.cpp',recipe['files'][str((parent.parent/'fixture.cpp').resolve())]).read_text()
    helper=r'''
static unsigned constructor_control_mode{},constructor_authored_owner{},constructor_authored_byte{};
static unsigned constructor_control_phase(){return constructor_control_mode>=8?14U:13U;}
static void constructor_protect(mw34::m4_runtime::Runtime&r,unsigned address,mw34::m4_runtime::Permissions p){for(const auto&v:r.image_metadata().mapped_regions)if(address>=v.start.value&&std::uint64_t(address)<std::uint64_t(v.start.value)+v.size){r.memory().protect(v.start,p);return;}throw std::runtime_error("Actual control address must own one admitted source image region");}
static void constructor_authored_before(mw34::m4_mixed::Context&c,unsigned phase){
 using namespace mw34::m4_runtime;DirectPhaseWriter::before(c,phase);if(phase!=constructor_control_phase())return;
 auto&r=c.runtime();auto&s=c.state();const auto mode=constructor_control_mode;
 if(mode==1)s.addr.ds_base.dword=4;
 if(mode==2){s.aflag.df=1;s.rflag.flat|=0x400;r.cpu().eflags|=0x400;}
 if(mode==3){constructor_protect(r,0x5bb4bc,Permissions::read|Permissions::write);r.memory().store<unsigned>({0x5bb4bc},0);constructor_protect(r,0x5bb4bc,Permissions::read);}
 if(mode==4){constructor_protect(r,0x4103f0,Permissions::read|Permissions::write);r.memory().store<std::uint8_t>({0x4103f0},r.memory().load<std::uint8_t>({0x4103f0})^1);constructor_protect(r,0x4103f0,Permissions::read|Permissions::execute);}
 if(mode==5)r.memory().protect(r.fs_base(),Permissions::read);
 if(mode==6)r.memory().protect({0x20001000},Permissions::read);
 if(mode==7){const auto header=r.memory().load<unsigned>({0x603fdc});need(header,"Current carried header must be genuinely nonzero");constructor_authored_owner=header;constructor_authored_byte=r.memory().load<std::uint8_t>({header});r.memory().store<std::uint8_t>({header},constructor_authored_byte^1);}
 if(mode==8){constructor_protect(r,0x5bcc80,Permissions::read|Permissions::write);r.memory().store<unsigned>({0x5bcc80},0x40a850^1);constructor_protect(r,0x5bcc80,Permissions::read);}
 if(mode==9){const auto n=r.memory().load<unsigned>({0x603fe0});need(n<255,"Finite carried whole list counter");r.memory().store<unsigned>({0x603fe0},n+1);}
 auto*w=DirectPhaseWriter::current;need(w,"Current ordinary controls writer");w->writer->append(w->prefix+"authored/State.bin",&s,3504);w->writer->append(w->prefix+"authored/CPU.bin",&r.cpu(),40);w->writer->append(w->prefix+"authored/FX.bin",r.fx().data(),512);
}
static void constructor_retry_snapshot(mw34::m4_mixed::Context&c,mw34::capture_direct::Writer&w,const std::string&p){
 w.append(p+"State.bin",&c.state(),3504);w.append(p+"CPU.bin",&c.runtime().cpu(),40);w.append(p+"FX.bin",c.runtime().fx().data(),512);
 for(auto address:mw34::m4_mixed::registration_pages){std::array<std::byte,4096>b{};c.runtime().memory().read({address},b);w.append(p+"page-"+std::to_string(address)+".bin",b.data(),4096);}
 for(auto address:mw34::m4_mixed::pages){std::array<std::byte,4096>b{};c.runtime().memory().read({address},b);w.append(p+"page-"+std::to_string(address)+".bin",b.data(),4096);}
 DirectPhaseWriter d{&w,p+"registry/"};c.registry().dump(&DirectPhaseWriter::sink,&d);
}
'''
    source=one(source,'int main(int argc,char**argv){try{',helper+'\nint main(int argc,char**argv){try{')
    source=one(source,'need(argc==6,"Joint130 exact game/numeric/CRT/MFC fresh-directory")','need(argc==7,"Current constructor controls exact game/numeric/CRT/MFC fresh-directory mode")')
    source=one(source,'capture_direct::Writer writer(argv[5],options);','capture_direct::Writer writer(argv[5],options);constructor_control_mode=unsigned(std::stoul(argv[6]));need(constructor_control_mode>=1&&constructor_control_mode<=9,"Exactly nine authored public source constructor refusal cases");')
    source=one(source,'const std::array<std::array<unsigned,3>,6>cases{{{0,0x7f,0},{0,0x37f,7},{0,0xf7f,0},{1,0x47f,7},{1,0xa7f,0},{1,0xe7f,7}}};','const std::array<std::array<unsigned,3>,1>cases{{{0,0x37f,7}}};')
    source=one(source,'context.before_phase=&DirectPhaseWriter::before;','context.before_phase=&constructor_authored_before;')
    start=source.index('  if(!ok){const std::string reason=')
    end=source.index('DirectPhaseWriter::current=nullptr;total+=records.size();++seq;',start)+len('DirectPhaseWriter::current=nullptr;total+=records.size();++seq;')
    replacement=r'''  need(!ok&&context.failed()&&context.runtime().poisoned()&&context.completed==constructor_control_phase(),"Actual authored constructor seam must reject at the exact selected chronology and retain first fault");
  const std::string reason=context.failure_reason();need(!reason.empty(),"Actual first refusal reason retained");writer.append(prefix+"refusal.txt",reason.data(),reason.size());
  constructor_retry_snapshot(context,writer,prefix+"retry-before/");const auto calls=context.runtime().calls().size();
  std::vector<Native>retry_records;Host retry_caller(static_cast<std::uint16_t>(cw));alignas(16)std::array<std::byte,1632>retry_hardware{};MFCConnectedGuarded retry{&context,seq,repeat,top,&retry_records,false};mfc_connected_hardware_call(&retry,retry_hardware.data());retry_caller.capture();
  need(!retry.completed&&context.runtime().poisoned()&&retry_records.empty()&&context.runtime().calls().size()==calls&&reason==context.failure_reason(),"Same poisoned actual Context refuses retry without progress or first-fault replacement");
  constructor_retry_snapshot(context,writer,prefix+"retry-after/");writer.append(prefix+"retry-hardware.bin",retry_hardware.data(),retry_hardware.size());
  // Refusal and unchanged retry above still retain the authored fault. Restore
  // only the three explicit input mutations needed to make cleanup writable;
  // do not repair a source field, effect, Runtime, State, FX, or owner witness.
  if(constructor_control_mode==5)context.runtime().memory().protect(context.runtime().fs_base(),m4_runtime::Permissions::read|m4_runtime::Permissions::write);
  if(constructor_control_mode==6)context.runtime().memory().protect({0x20001000},m4_runtime::Permissions::read|m4_runtime::Permissions::write);
  if(constructor_control_mode==7){need(constructor_authored_owner&&context.runtime().memory().load<std::uint8_t>({constructor_authored_owner})==(constructor_authored_byte^1),"Only the exact still-authored mirror byte is restored for cleanup");context.runtime().memory().store<std::uint8_t>({constructor_authored_owner},std::uint8_t(constructor_authored_byte));}
  const std::array<unsigned,4>repair{constructor_control_mode,constructor_authored_owner,constructor_authored_byte,unsigned(constructor_control_mode>=5&&constructor_control_mode<=7)};writer.append(prefix+"cleanup-input-restoration.bin",repair.data(),sizeof(repair));
  DirectPhaseWriter cleanup{&writer,prefix+"cleanup/"};context.registry().finish();context.registry().dump(&DirectPhaseWriter::sink,&cleanup);need(!context.registry().live_handle(),"Actual surviving carried MFC/CRT owners must be released after refusal");
  const std::array<unsigned,8>status{1,constructor_control_mode,unsigned(!ok),unsigned(!retry.completed),unsigned(context.runtime().poisoned()),unsigned(calls),unsigned(context.runtime().calls().size()),unsigned(context.completed)};writer.append(prefix+"control-status.bin",status.data(),sizeof(status));DirectPhaseWriter::current=nullptr;++seq;'''
    source=source[:start]+replacement+source[end:]
    source=one(source,'need(seq==6&&total==222,"Exact connected130 schedule")','need(seq==1,"Exactly one current authored constructor control attempt/retry")')
    source=source.replace('Six measured37-root sequences and actual owned cleanup complete; fullM4 incomplete','Current authored constructor refusal, unchanged poisoned retry and surviving actual owner cleanup complete; fullM4 incomplete')
    (out/'fixture.cpp').write_text(source)
    policy=dict(cases=[dict(mode=i,target_phase=14 if i>=8 else 13,target_root=0x410440 if i>=8 else 0x4103f0,mutation=m)for i,m in enumerate(['nonflat DS','reverse DF','own raw ordinal823 import','actual root opcode preimage','source FS-head write permission','actual source stack write permission','whole carried guest owner mirror byte','readonly current getter target slot','whole current source list count'],1)],source_machine_repaired_for_retry=False,retry_on_same_poisoned_Context=True,retry_scope='All emitted State3504/CPU40/FX512/46 whole source pages/provider exports, no hidden Runtime or permission-byte equality claim',cleanup_scope='Actual surviving source generations/current private owners after exact authored FS/stack permission or mode7 mirror-byte input restoration only; emitted separately, no source-effect repair or fabricated capacity',native_physical_capacity_inferred=False,source_registration_or_API_response_seeds=False)
    (out/'control-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
    for p in out.rglob('*'):
        if p.is_file():pin(p)
    pin(__file__)
    report=dict(recipe);report.update(passed=True,scope='Uncompiled nine public current constructor refusal/retry/owned-cleanup ordinary workers; preparation only, no actual denial claim',parent_preparation_path=str(parent),parent_preparation_sha256=sha(parent),control_modes=9,source_sequences=1,source_AFTER_seed=False,native_executed=False,initializer_credit=0,files=files)
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(p),sha256=sha(p),control_modes=9,native_executed=False)))
if __name__=='__main__':main(sys.argv[1])
