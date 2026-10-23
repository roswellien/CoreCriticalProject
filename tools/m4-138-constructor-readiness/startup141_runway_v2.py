"""Read-only bounded141 composition readiness; no runnable recipe or capture."""
from pathlib import Path
import difflib,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup141-runway'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 positive=read(R/'reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a')
 fixture=read(R/'reports/m4-constructor-native/fixture-preparation-r6/report.json','f0dfc1427c9cca0c1b920be6fc030c6b9bb7e53ef631946abcbf4ddf215001a0')
 validation=read(R/'reports/m4-constructor-native/fixture-validation-r4/report.json');assert validation['passed']and validation['build_sha256']=='0f5761af58092ef55ccd265ed0acf5a0bbdead40fab96cdb87eccb79f99f1d18'and validation['preparation_sha256']==sha(R/'reports/m4-constructor-native/fixture-preparation-r6/report.json')and not validation['initializer_credit']
 assert validation['execution_sha256']=='a3945f68857cced5af2b946302ddf92992b2ba4d1440e3fad0e266ab4e9801e6'
 pin(validation['execution_path'],validation['execution_sha256'])
 service=read(R/'reports/m4-constructor-native/service-preparation-r8/report.json','7437fa44e96c0ad7ec07431b8b69c00e08e63a8be139827bf7e1e11caaa53140')
 source=read(R/'reports/m4-constructor-native/preparation-r6/report.json','7d880b421d15d6de0723182c789a521a33763cf2e97ebb74b2f809f0f8622635')
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 game=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes());off=pe.rva_range(0x5e0000-pe.image_base,0x244)[0]
 raw_table=pe.data[off:off+0x244];order=[dict(slot=0x5e0000+4*i,entry=v)for i,(v,)in enumerate(struct.iter_unpack('<I',raw_table))if v];assert len(order)==144
 ct={0x4103f0,0x410440,0x459b40};accepted_selection=positive['selected_order'];neworder=[row for row in order if row in accepted_selection or row['entry']in ct];assert len(neworder)==141
 assert [row for row in neworder if row['entry']not in ct]==accepted_selection
 insertions=[]
 for phase,row in enumerate(neworder):
  if row['entry']in ct:
   oldphase=next(i for i,x in enumerate(fixture['selected_order'])if x['entry']==row['entry']);insertions.append(dict(phase141=phase,phase37=oldphase,physical_slot=row['slot'],entry=row['entry']))
 assert [(r['phase141'],r['entry'])for r in insertions]==[(13,0x4103f0),(14,0x410440),(39,0x459b40)]
 # Every service input examined is physical and bound by its preparation.
 fps=Path(positive['borrowed_service_preparation']).parent;fp=read(fps/'report.json',positive['borrowed_service_preparation_sha256']);ctor=Path(service['native_include'])
 shared=sorted({p.name for p in fps.iterdir()if p.is_file()and p.name!='report.json'}&{p.name for p in ctor.iterdir()if p.is_file()and p.name!='report.json'});relations=[];deltas=[]
 for n in shared:
  a=pin(fps/n,fp['files'][str((fps/n).resolve())]);b=pin(ctor/n,service['files'][str((ctor/n).resolve())]);same=a.read_bytes()==b.read_bytes();relations.append(dict(file=n,positive_sha256=sha(a),constructor_sha256=sha(b),whole_bytes_equal=same))
  if not same:deltas.append(dict(file=n,unified_diff='\n'.join(difflib.unified_diff(a.read_text().splitlines(),b.read_text().splitlines(),fromfile=str(a),tofile=str(b)))+'\n'))
 assert {x['file']for x in deltas}=={'session_impl.inc','session.hpp','locale_batch.hpp','fs_operations.inc'}
 fps_impl=(fps/'session_impl.inc').read_text();ctor_impl=(ctor/'session_impl.inc').read_text()
 assert 'case 0x40f000:callback=0x40f030;'in fps_impl and 'case 0x40f000:callback=0x40f030;'not in ctor_impl
 assert 'Current live producer full-byte cursor before literal msize, including a full vector'in fps_impl and 'One bounded literal registry growth per widget registration'in fps_impl
 assert 'Current live producer full-byte extent before literal msize'in ctor_impl
 for n in ['fixture.cpp','constructor_component.hpp','constructor_session.hpp','root-bindings.json','source-delta.json']:
  p=R/'reports/m4-constructor-native/fixture-preparation-r6'/n;pin(p,fixture['files'][str(p.resolve())])
 for n in ['component.cpp','component.hpp','literals.hpp']:
  p=R/'reports/m4-constructor-native/preparation-r6'/n;pin(p,source['files'][str(p.resolve())])
 for n in ['native_main.cpp','joint_protocol.hpp','onexit_session.hpp']:
  p=R/'reports/m4-joint-startup138/preparation-r4'/n;pin(p,positive['files'][str(p.resolve())])
 for n in ['constructor_store_contract.inc','constructor_store_operands.hpp','constructor-FS-contracts.json','free-restore-contract.json']:
  p=ctor/n;pin(p,service['files'][str(p.resolve())])
 pin(R/'tools/m4-constructor-native/prepare_fixture_v4.py');pin(R/'tools/analysis/pe.py');pin(__file__);pin(sys.executable)
 readiness=dict(passed=True,scope='Bounded source/physical-order141 composition runway only; explicit service integration conflict prevents executable recipe',
  proposed_selected_roots=141,accepted_count=131,total_inventory_roots=144,initializer_credit=0,executable_preparation_created=False,build_executed=False,native_executed=False,archive_reader_opened=False,
  exact_insertions=insertions,remaining_unselected=[x for x in order if x not in neworder],full_141_source_or_original_equivalence_proved=False,
  service_shared_files=len(shared),unchanged_shared_files=sum(x['whole_bytes_equal']for x in relations),service_changed_files=[x['file']for x in deltas],service_source_relations=relations,
  immediate_blocker='Constructor service8 regresses current138 shared borrowed-onexit adapter: missing FPS0x40f000 mapping and excludes full-vector registry growth; neither dual static-library Session copies nor direct service substitution preserves current semantics.',
  exact_required_delta=[
   'Derive one additive service union from current138 fps service3: retain exact entire grow/no-grow owner/capacity/HeapSize/HeapReAlloc/full-byte guards; preserve all7widget/FPScallback mappings and add only constructors4103f0→410420,410440→410470,459b40→459b70.',
   'Add constructor8 Session scope/prior-read/store/full-owner mirror methods and Binding constructor_source_root plus exact physical CRT allocator/free balanced-journal FS admission. Keep inherited shared code unchanged except these reviewed seams; one same Session and one same native heap owner.',
   'Compose current138 Context with one lazy persistent constructor Component borrowing that Session; carry existingRuntime State/FX and committed CALL atframe20001800/broker410a80. Register exactly3root callbacks beforefreeze, using existing29byte physicalroot/COFF provenance.',
   'Integrate literalMFC823/825 calls at existing source sites via exact rawIAT5bb4bc=80000337 and5bb4c8=80000339, exact argument/frame return. Preserve actual12/4byte role requests, allocation generation/capacity/whole mirror and genuineNULL free; no copied observations or graph seeds.',
   'Preserve getter40a850 currentread-only vptr+18 dispatch, liveowner603fdc header/603fe0 count, allforward/backlinks, count+1graph and exactlyone matchingreceiver. Its37fixture predecessorgraph is not assumed for full141 chronology.',
   'Preserve full138 widget mapping/GDI/formatter/pages/association cleanup and growth replay. Constructorowner cleanup joins same Session finish after widget-owned fonts cleanup; observe all constructor/owner/sourceframe/FS/getter records and global5f2000 eachphase.',
   'Generate physical slot-sorted141table;6domains give846phases. Route invariants become141selectedroots+3inheritednumeric/SPIextra calls=144calls,142translations and111registeredcallbacks. Fixed Native159716 format stays; independently measure actualcounts.',
   'Build freshO0/O2 mergedservice/component/fullworkers with existing compiler. Require exactinverse deltas plus wholeCOFF/currenttyped bridge/import/ASM/TLS/linkedtarget/header review and fresh prelaunch before execution.',
   'Require new whole141native/source/provider/GDI/caller/cleanup/controls and originalpaired domains before credit. Successful37structural validation is reusable evidence but literal original/source evaluator and faultcontrols remain pending.'
  ],prior_evidence_scope=validation['scope'],files=pins)
 out.mkdir(parents=True);(out/'selected-order141.json').write_text(json.dumps(neworder,indent=2)+'\n');(out/'service-conflict-deltas.json').write_text(json.dumps(deltas,indent=2)+'\n');(out/'physical-table144.json').write_text(json.dumps(dict(table_address=0x5e0000,bytes=0x244,sha256=hashlib.sha256(raw_table).hexdigest(),nonzero_order=order),indent=2)+'\n')
 for p in out.iterdir():pin(p)
 q=out/'report.json';q.write_text(json.dumps(readiness,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),executable_recipe=False,insertions=insertions)))
if __name__=='__main__':main(sys.argv[1])
