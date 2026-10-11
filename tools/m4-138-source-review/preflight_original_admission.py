"""Bounded definition/physical-input preflight; opens no capture reader."""
from pathlib import Path
import ast, hashlib, importlib.util, json, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PREP='8308fe8ceaaae3fbb07b2f7204bd167c495dbffd5f281fed95d83c2b4a90f7f8'

def main(name):
 out=ROOT/'reports/m4-joint-startup138-source'/name
 if out.exists():raise ValueError('Fresh immutable source preflight')
 out.mkdir(parents=True);pins={};reads=set();passed=False;details={}
 def need(value,message):
  if not value:raise ValueError(message)
 def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
 def pin(path,digest=None):
  path=Path(path).resolve();need(path.suffix.lower()not in('.mwb','.zip','.mwi'),'No archive/index input admitted')
  actual=sha(path);need(digest is None or actual==digest,'Exact physical source input '+str(path));need(str(path)not in pins or pins[str(path)]==actual,'Stable input identity')
  pins[str(path)]=actual;return path
 def audit(event,args):
  if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
  path=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
  reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
  if not reading:return
  need(path.suffix.lower()not in('.mwb','.zip','.mwi')and path.name not in('transport.json','bundle.json','manifest.json'),'No canonical payload/index/transport opened by definition preflight')
  if path.is_relative_to(ROOT)and path.is_file():reads.add(str(path))
 sys.addaudithook(audit)
 try:
  preparation=pin(ROOT/'reports/m4-joint-startup138-source/preparation-r3/report.json',PREP)
  p=json.loads(preparation.read_bytes());need(p['passed']and p['writer_executed']is False and p['capture_archive_reader_opened']is False and p['initializer_credit']==0,'Exact unexecuted source-only preparation')
  for path,digest in p['files'].items():pin(path,digest)
  entry=pin(p['entrypoint']);tree=ast.parse(entry.read_text());need(not any(isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='main'for node in tree.body),'Main is guarded, not executed on import')
  spec=importlib.util.spec_from_file_location('source138_definition_preflight',entry);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  need(len(module.PAGES)==69 and len(set(module.PAGES))==69 and module.PAGES[:43]==module.LEGACY_PAGES,'All whole source pages with immutable accepted numeric order')
  need(module.FRAME==0x20001800 and module.BROKER==0x410a80,'Exact current caller interface')
  need(Path(module.EX.__file__).resolve()==entry.parent/'paired_exports.py','Explicit physically generated current paired export helper')
  need(module.EX.selected('sequence-0/Widget/root-4252240/carried-before/State.bin'),'Complete current Widget equality targets exported')
  delta_path=pin(entry.parent/'original-admission-delta.json')
  delta=json.loads(delta_path.read_bytes());parent=pin(ROOT/'reports/m4-joint-startup138-source/preparation-r2/compare_provider138.py')
  current=entry.read_text();need(current.count(delta['new'])==1 and current.replace(delta['new'],delta['old'])==parent.read_text(),'Independent exact inverse retains every parent source gate')
  need(current.index('required_original=dict(')<current.index('ori=D.DirectSet(') and current.index("original_counts['widget_exact_MFC_CRT_transition_page_relations']==768")<current.index('ori=D.DirectSet('),'Complete original identity/count guards before canonical reader')
  pin(ROOT/'tools/m4-startup138-original/validate_v3.py','e1f7e0384f2a00853af1a96418731be67db76bf103512302ef4e0e679a47a69b')
  pin(ROOT/'tools/m4-138-source-review/prepare_original_admission_preflight.py','ced7e344bb1c7ecf46d1a1b5689ff2d706d390acbc209ee6d0f61121eb7277af')
  need(module.PW.WIDGETS==(0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0),'Literal table-sorted current widget order')
  spec=importlib.util.spec_from_file_location('source138_literal_model_preflight',ROOT/'reports/m4-fps-original/source-preparation-r4/game_model.py');game=importlib.util.module_from_spec(spec);spec.loader.exec_module(game)
  program,callbacks=game.source_program()
  contracts_path=pin(ROOT/'reports/m4-fps-native/connected-component-preparation-r4/contracts.json');literals_path=pin(ROOT/'reports/m4-fps-native/connected-component-preparation-r4/literals.hpp')
  contracts=json.loads(contracts_path.read_bytes());geometry=module.PG.ContractGeometry(contracts,literals_path.read_text())
  # The declared callback provider merge is the frozen bootstrap's responsibility.
  # This bounded pass authenticates its consumed material without executing it.
  provider_contract=pin(ROOT/'reports/m4-onexit-review/interface-r1/instruction-contracts.json')
  provider=json.loads(provider_contract.read_bytes());provider_rows=provider['instructions']if isinstance(provider,dict)else provider
  for row in provider_rows:
   need(row['pc']not in program or program[row['pc']]==row,'Every shared source/provider instruction collision is exact')
  source=entry.read_text()
  for marker in('PW.checkpoint_index','PW.machine_class','association.begin(entry)','G.complete_root(machine,api=leaf)','association.end()','association.cleanup(GI)','association.prove_projection_rows','machine.fx=projection(m,machine.state)[0]','F.finish(machine,responses,expected_callbacks,G)','FC.check(self,row,self._source_undefined_flags)','MF.Extension(joint131,pin)'):
   need(marker in source,'Preserved complete current source obligation '+marker)
  need("counts['whole_page_BEFORE']==counts['whole_page_AFTER']==1656*69"in source,'Complete every-phase whole-page endpoint predicate')
  # Do not authenticate by a broad path replacement: frozen parent paths stay exact.
  need("reports/m4-joint-startup131"not in str(entry),'Current executed comparer path is additive')
  details=dict(source_phases=1656,source_cases=12,source_roots=138,whole_source_pages=69,
   literal_model_rows=len(program),literal_model_callback_PCs=len(callbacks),registry_provider_rows=len(provider_rows),
   component_geometry=geometry.summary(),source_journal_domains=2,shared_CALL_operands_per_widget=2,
   complete_literal_GDI_leaf_calls_per_sequence=149,manual_owned_font_frees_per_sequence=15,
   carried_machine_or_source_program_executed=False)
  for path in sorted(reads-set(pins)):pin(path)
  need(reads<=set(pins),'All actual successful bounded workspace reads physically pinned')
  pin(__file__);pin(sys.executable)
  for path,digest in list(pins.items()):need(sha(path)==digest,'Every bounded input unchanged at completion')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,preparation_sha256=PREP,scope='Independent bounded generated definitions/import/finite source geometry preflight; source machine and capture readers are never executed',
   counts=details,actual_successful_workspace_reads=len(reads),archive_reader_opened=False,worker_launched=False,
   source_machine_executed=False,native_result_equivalence=False,initializer_credit=0,files=pins)
  path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(path),sha256=sha(path),physical_inputs=len(pins),counts=details)))

if __name__=='__main__':main(sys.argv[1])
