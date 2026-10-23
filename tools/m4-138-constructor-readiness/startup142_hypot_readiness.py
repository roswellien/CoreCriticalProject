"""Bounded ordinary-only142 hypot integration runway, not execution admission."""
from pathlib import Path
import hashlib,json,struct,sys,re
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup142-runway/readiness-r1';assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.zip','.mwb');v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 parent=R/'reports/m4-startup141-runway/preparation-r2';p=read(parent/'report.json','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c')
 read(R/'reports/m4-startup141-runway/order-relation-correction-r1/report.json','ec825380cf4fde43fcf4ab9bdd67b16324ffa99d08cfde06545f716f4e39fbf5')
 parentbuild=read(R/'reports/m4-startup141-runway/build-r2/build.json','0c00c2fe8857e9785043c6946920287644521efafe4830a75787f1f6b26f6032')
 fixture=R/'reports/m4-hypot-native/fixture-preparation-r6';f=read(fixture/'report.json','7219937e27edf2960129466f6416bfe109bee5b03f4e702c103fa296d80db03a')
 evidence={}
 for name,path in dict(build='reports/m4-hypot-native/fixture-build-r6/build.json',whole_state='reports/m4-hypot-native/whole-state-r3/report.json',comparison='reports/m4-hypot-native/fixture-comparison-r2/report.json',refusals='reports/m4-hypot-native/fixture-refusals-r1/report.json',review='reports/m4-tree-review/hypot-current-review-r4/report.json').items():
  q=R/path;v=read(q);assert v['passed'];evidence[name]=dict(path=str(q.resolve()),sha256=sha(q),scope=v.get('scope'),counts=v.get('counts'))
 assert evidence['build']['sha256']=='9d36ad08985ecac2e28711cd2d9e3295b959eadd90524258ad166540c4f3f7dd'
 assert evidence['comparison']['sha256']=='9017ac858319ea841b879b05bf0aa551140aa61d9bc7507b9f0efb48003e49b5'
 for n in ['fixture.cpp','fixture_spec_O0.hpp','fixture_spec_O2.hpp','generated_bridges.inc','literal_dispatch.hpp','control_runtime.cpp','CMakeLists.txt','hardware_boundary.obj']:
  q=fixture/n;pin(q,f['files'][str(q.resolve())])
 for n in ['native_main.cpp','joint_protocol.hpp','selected-order.json','CMakeLists.txt']:
  q=parent/n;pin(q,p['files'][str(q.resolve())])
 # Re-read the physical PE table, not a captured endpoint or inferred name.
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 q=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(q.read_bytes());off=pe.rva_range(0x5e0000-pe.image_base,0x244)[0];raw=pe.data[off:off+0x244]
 physical=[dict(slot=0x5e0000+4*i,entry=v)for i,(v,)in enumerate(struct.iter_unpack('<I',raw))if v];assert len(physical)==144
 order=[x for x in physical if x in p['selected_order']or x['entry']==0x4b5910];assert len(order)==142 and [x for x in order if x['entry']!=0x4b5910]==p['selected_order']
 phase=next(i for i,x in enumerate(order)if x['entry']==0x4b5910);placement=dict(phase142=phase,phase144=next(i for i,x in enumerate(physical)if x['entry']==0x4b5910),**order[phase],previous=order[phase-1],following=order[phase+1]);assert placement['slot']==0x5e0154
 roff=pe.rva_range(0x4b5910-pe.image_base,5)[0];root=pe.data[roff:roff+5];jump=0x4b5915+struct.unpack('<i',root[1:])[0];assert root[0]==0xe9 and jump==0x4b5920
 code=(fixture/'fixture.cpp').read_text();parentcode=(parent/'native_main.cpp').read_text();required=['std::memset(&c.s,0,sizeof(c.s))','hf::initial_flags','Runtime::external_return','API_count < 2','a.frame+4','c.s.gpr.rip.dword==0x4b5905','a==0x60b2e8','reinterpret_cast<const std::byte*>(&c.s)+2486','(proof.actual_SW>>9)&1','mask==127','need(seq<6','need(count==190']
 assert all(x in code for x in required);assert 'no State/FX/page/owner reseed'in parentcode and 'constructor_entry'in parentcode
 spec=(fixture/'fixture_spec_O0.hpp').read_text();assert 'std::array<AccessSpec,616>'in spec
 operands=[dict(pc=int(a),address=int(b),width=int(c),writing=int(d))for a,b,c,d in re.findall(r'\{(\d+)U,(\d+)U,(\d+)U,(\d+)U\}',spec)];assert len(operands)==616
 fixedstack=[x for x in operands if 0x20001000<=x['address']<0x20002000];globalswritten=sorted({(x['pc'],x['address'],x['width'])for x in operands if x['writing']and not(0x20001000<=x['address']<0x20002000)})
 pin(R/'tools/analysis/pe.py');pin(__file__);pin(sys.executable);out.mkdir(parents=True)
 for n,v in [('selected-order142.json',order),('literal-store-inventory.json',dict(nonstack_source_writes=[dict(pc=pc,address=a,width=w)for pc,a,w in globalswritten],all_source_operands=616,fixed_stack_operands=len(fixedstack)))]:
  q=out/n;q.write_text(json.dumps(v,indent=2)+'\n');pin(q)
 report=dict(passed=True,scope='Bounded physical/source142 hypot integration readiness only; direct standalone fixture reuse demonstrably reseeds carried state, so executable derivative and compile deliberately not prepared without source proof',accepted_count=131,initializer_credit=0,native_executed=False,archive_reader_opened=False,worker_launched=False,build_executed=False,execution_admitted=False,portable_component_already_available=False,proposed_selected_roots=142,proposed_phases=852,placement=placement,physical_table_sha256=hashlib.sha256(raw).hexdigest(),root_bytes=root.hex(),root_sha256=hashlib.sha256(root).hexdigest(),root_literal_jump_target=jump,remaining_physical_roots=[x for x in physical if x not in order],reusable_standalone_evidence=evidence,
  exact_observed_blockers=[
   'Standalone native_root memset resets entire State3504, overlays fresh runtimeCPU/FX and hardcodes segment values; main preloads190 genuine BEFORE pages and six entryCPU40/FX512/ENV28 snapshots. These operations cannot occur within carried142.',
   'Standalone Context cpu() initializes unmodeled EFLAGS from constant202; final return admission/frame is Runtime::external_return. Carried entry must preserve actual State/rflags/defined aflags and actual committed outerCALL broker410a80 frame20001800.',
   'Finite616 access specs include fixed absolute stack addresses and reached-PC branch inventory proven for six standalone inputs. No proof in these examined files that current carried141 predecessor FP/rawmemory/controller state selects exactly this admitted domain.',
   'Standalone measured empty source x87 stack ftw0 and CW-owned hardware Isolation require actual carried-before verification across sixdomains; existing standalone caller restoration does not prove carried142 hardware domain.',
   'No standalone portable borrowing Component API exists: callbacks use process-global numeric active token, direct dump paths, Runtime invoke/hardware wrappers and separate executable main. Whole-current141 callback/linked-target/header/ASM/TLS review remains pending.'
  ],exact_required_delta=[
   'Factor literal numeric callbacks into one Component borrowing existing142Runtime/State/Memory with an explicit admission gate and sink; preserve all21 literal bodies/fragments and generated typed/raw80 numerical bridges. No new arithmetic endpoint oracle.',
   'Borrow actual sourceCALL at root4B5910; initialize local frame journal from actual committed stack bytes/broker only. Preserve State3504,CPU40,FX512 and all carried pages/owners; only source instructions/finite hardware-derived FP field seams may mutate.',
   'Admit actual carried-before numerical input globals, sourceCW/TOP/tag/raw80 and actual stack footprint against physical/literal control domain. Reject unsupported changed branch/input domains; prove scope before reusing616operand schedule. Do not transplant standalone BEFORE pages or assume sixsequence index proves matching inputs.',
   'Join exactly two source cdecl7802A122 hypot intervals with actual callsite/return bytes, fullState/CPU,32Bargumentframes and stack4096 before/after, RET4 and literal caller cleanup. Both use retained physical CRT module ownership and exact IAT identity, not DLL name alone.',
   'Retain every literal globalstore from inventory. FinalFSTP sourcePC4B5905→60B2E8 must read exact current raw80ST0 bytes atState2486 length10, sourceCW-owned fldt/fstps/fnstsw; prove actual loweredF32equals hardwareF32 and update only sourceC1 fromactualSWbit9. Keep raw8010B stores and FNSTSW16 relations exact.',
   'Preserve mask127 clear/test controls, raw80sqrt typed primitive and actual hostFX512/ENV28 restoration around borrowed call; do not substitute compiler intermediates for sourceFSTPC1.',
   'Add one registered4B5910 callback beforefreeze and physical slot5E0154 only; existing141fullchronology/rootcallbacks/servicegrowth unchanged. Extend numeric/global/API/source/caller observations and refusals, poison/retry/private witnesses to current142 worker.',
   'Build freshO0/O2 borrowing component/unionworkers using existing toolchain only after source inverse/finiteIR equivalence and carriedinput domain proof. Independent wholeCOFF/full-link typedtarget/ASM/TLS/currentdependencies and prelaunch required before any native worker.',
   'Require new142source/provider/raw/originalwhole-state/API/FP/hardware/cleanup/controls evidence before accepted credit. Standalonebuild6/currentreview4 provide reusable finite evidence, not carried142 equivalence.'
  ],bounded_validation='Pinned only listed ordinary report/source/files and physical PE table/root. No exhaustive report-files traversal, capture reread, canonical reader, native or verifier execution.',files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),placement=placement,passed=True,execution_admitted=False)))
if __name__=='__main__':main()
