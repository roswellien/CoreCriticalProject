"""Freeze a minimal additive original138 observation validator; open no captures."""
from pathlib import Path
import ast,hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PREP='e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2'
BUILD='748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69'
REVIEW='efaa5d25802440f8cd47092d16a0368084cf5ea744d8c2cda5c826522f96122a'
SOURCE_REVIEW='341f656ac7c4d45ca4f9574d1884a2783ddc070779269878fea22091e43137e2'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def main(name):
 out=R/'reports/m4-startup138-original'/name;need(not out.exists(),'Fresh validation preparation only');files={};changes=[]
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip')and p.name not in('payload.bin','index.json','transport.json'),'Ordinary preparation inputs only');d=sha(p);need(h is None or d==h,'Exact ordinary input '+str(p));need(str(p)not in files or files[str(p)]==d,'One immutable physical identity');files[str(p)]=d;return p
 prep=R/'reports/m4-startup138-original/preparation-r7';build=R/'reports/m4-startup138-original/build-r4/build.json';review=R/'reports/m4-tree-review/original138-prelaunch-r5/report.json'
 p=json.loads(pin(prep/'report.json',PREP).read_bytes());b=json.loads(pin(build,BUILD).read_bytes());q=json.loads(pin(review,REVIEW).read_bytes());s=json.loads(pin(R/'reports/m4-tree-review/original138-source-r2/report.json',SOURCE_REVIEW).read_bytes())
 need(all(v['passed']for v in(p,b,q,s))and b['preparation_sha256']==PREP and q['build_sha256']==BUILD,'Current reviewed worker lineage')
 spec=pin(prep/'spec.hpp').read_text();m=re.search(r'std::array<unsigned,69> widget_whole_pages\{([^}]+)\};',spec);need(m is not None,'Physical compiled source69 inventory');whole=[int(x.strip(),16)for x in m[1].split(',')]
 need(len(whole)==len(set(whole))==69 and whole[:43]==p['observed_pages']and set(whole[43:])==set(p['extra_whole_source_pages']),'Exact compiled order and source inventory agreement')
 contract=json.loads(pin(prep/'contracts.json').read_bytes());need((contract['whole_source_pages'],contract['original_fixed_pages'],contract['extra_whole_page_endpoints'])==(69,43,26),'Contracts remain count-only')
 parent=R/'tools/m4-startup131-original/validate_v4.py';text=pin(parent).read_text()
 def replace(a,z,count=1):
  nonlocal text
  need(text.count(a)==count,'Unique explicit inherited adaptation '+a[:80]);changes.append(dict(before=a,after=z,occurrences=count));text=text.replace(a,z)
 replace('"""Authenticate actual original131 bootstrap, Lockit frames, owners and schedule."""','"""Authenticate original138 observations while preserving all inherited131 checks."""')
 replace("BASE=ROOT/'reports/m4-startup131-original'","BASE=ROOT/'reports/m4-startup138-original'")
 replace("sys.path.insert(0,str(Path(__file__).resolve().parent));from mfc_phase_v3 import observe as observe_mfc,constructor as observe_constructor", "sys.path.insert(0,str(ROOT/'tools/m4-startup131-original'));from mfc_phase_v3 import observe as observe_mfc,constructor as observe_constructor\nsys.path.insert(0,str(Path(__file__).resolve().parent));from widget_phase import Observer,ROOTS as WIDGET_ROOTS,PHASES as WIDGET_PHASES\nsys.path.insert(0,str(ROOT/'tools/m4-joint-startup131'));from paired_exports import Export\nsys.path.insert(0,str(ROOT/'tools/m4-pipeline'));from paths_capture_storage import STORAGE_ROOT")
 replace("def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()", "def sha(p):\n with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()")
 replace("out=BASE/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False;counts=Counter()", "out=BASE/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False;counts=Counter();paired_exports=[];export=None;transport=None")
 replace("  b=read(pin(build,digest));need(b['passed'],'Actual x86 build');", "  need(build==ROOT/'reports/m4-startup138-original/build-r4/build.json'and digest=='"+BUILD+"'and preflight_path==ROOT/'reports/m4-tree-review/original138-prelaunch-r5/report.json'and preflight_digest=='"+REVIEW+"','Exact current admitted original138 worker only')\n  b=read(pin(build,digest));need(b['passed'],'Actual x86 build');")
 replace("p['original_roots']==131,'Exact original131 ABI/order'", "p['original_roots']==138 and b['preparation_sha256']=='"+PREP+"','Exact original138 ABI/order'")
 replace("len(p['order'])==131 and", "len(p['order'])==138 and")
 replace("not in(0x5ae3e4,0x4b64f0,0x4df610,0x4e0710,0x4e0810,0x4e1ca0)", "not in(0x5ae3e4,0x4b64f0,0x4df610,0x4e0710,0x4e0810,0x4e1ca0,*WIDGET_ROOTS)")
 replace("'Exact accepted125 relative order plus five physical slots'", "'Exact accepted125 relative order plus current physical source additions'")
 replace("'Actual original131 execution'", "'Actual original138 execution'")
 replace("readerpath=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py')", "readerpath=pin(ROOT/'tools/m4-crt-allocation-root/run_storage.py')")
 replace("records=ds.DirectSet(e/'original/transport.json',pin)", "transport=Path(run['original_capture']).resolve();need(transport.is_relative_to(STORAGE_ROOT/'reports/m4-startup138-original')and transport.name=='transport.json','Declared G original capture only');records=ds.DirectSet(transport,pin)")
 replace("b'MW4J131O'and struct.unpack_from('<6I',header,8)==(1,6,131,786,43,356992)", "b'MW4J138O'and len(header)==32 and struct.unpack_from('<6I',header,8)==(1,6,138,828,43,356992)")
 replace("need(len(callback_byentry)==101,'101 exact recovered callback source domains')", "need(len(callback_byentry)==101,'All101 inherited recovered callback source domains')\n   widget_plan=read(ROOT/'reports/m4-fps-original/preparation-r1/normal-contracts.json')\n   for row in widget_plan['roots']:need(row['root']not in callback_byentry,'Distinct new literal callback');callback_byentry[row['root']]=row['callback']\n   need(len(callback_byentry)==108 and tuple(order[i]['entry']for i in WIDGET_PHASES)==WIDGET_ROOTS,'All108 literal callbacks and sorted seven-root chronology')")
 old="obs=read(Path(preflight_path).parent/'compiled-observers.json');format_shims={r['symbol']:r['target']for r in obs if r['family']=='format'};"
 new="""obs=read(Path(preflight_path).parent/'compiled-observers.json');resolutions={}
   for row in obs:
    for rel in row['relocations']:
     if rel['symbol_section']==0 and rel['resolution_kind']=='virtual address':
      symbol,value=rel['symbol'],rel['actual_symbol_address'];need(symbol not in resolutions or resolutions[symbol]==value,'Unique actual linked symbol identity');resolutions[symbol]=value
   format_shims={symbol:resolutions[symbol]for symbol in('_format_entry_strrchr','_format_entry_malloc','_format_entry_sprintf')};format_section=next(row for row in obs if row['family']=='whole-ASM'and row['symbol']=='format_observer_x86 whole source');need(all(format_section['address']<=v<format_section['address']+format_section['bytes']for v in format_shims.values()),'All three actual entry targets lie inside the wholly attributed current format observer');"""
 replace(old,new)
 anchor="   geometry=[];snapshot_rows=[];allowners=[];mfc_artifacts=[];constructor_artifacts=[]\n"
 added="""   contract=read(prep/'contracts.json');compiled_spec=pin(prep/'spec.hpp').read_text();match=re.search(r'std::array<unsigned,69> widget_whole_pages\\{([^}]+)\\};',compiled_spec);need(match is not None,'Current physically compiled source page order');whole=[int(x.strip(),16)for x in match[1].split(',')];need(whole[:43]==pages and len(set(whole))==69 and set(whole[43:])==set(p['extra_whole_source_pages']),'Source69 order/count agreement')
   fs_bindings={row['PC']:row for row in read(prep/'fs-hook-bindings.json')};need(len(fs_bindings)==93,'Every current exact source FS opcode binding')
   identity=struct.unpack('<15I',records.data('widget/identity.bin'));widget_targets=[];widget_section=next(row for row in obs if row['family']=='whole-ASM'and row['symbol']=='widget_observer_x86 whole source')
   for i,cell in enumerate((0x5bb070,0x5bb074,0x5bb068)):
    field,target,shim,declared,owner=identity[i*5:(i+1)*5];need(field==cell and target and declared and owner and widget_section['address']<=shim<widget_section['address']+widget_section['bytes'],'Actual GDI named loader target, module and wholly attributed observer range');widget_targets.append(target)
   fps_identity=struct.unpack('<4I',records.data('fps/identity.bin'));need(fps_identity==(0x5bb53c,0x780230dd,resolutions['_fps_entry'],0x78000000),'Actual staged named vsprintf and exact linked FPS entry target')
   widget=Observer(records,contract,whole,pages,fs_bindings,counts,widget_targets,fps_identity[1])
"""
 replace(anchor,anchor+added)
 replace("    carried=[];owners=[];formats={};mixed={}", "    carried=[];owners=[];formats={};mixed={};widget.begin_sequence(seq)")
 replace("'Authentic successful131 phase tag and host restore'", "'Authentic successful138 phase tag and host restore'")
 replace("counts['phases']+=1\n", "counts['phases']+=1;widget.phase(data,seq,phase,entry)\n")
 replace("struct.pack('<101I'", "struct.pack('<108I'")
 replace("'Complete15 owners and97 callbacks per sequence'", "'Complete15 inherited owners and108 literal callbacks per sequence'")
 replace("    cleanup_family(records,seq,formats,mixed,counts)\n", "    cleanup_family(records,seq,formats,mixed,counts);widget.cleanup(seq)\n")
 replace("counts['phases']==786", "counts['phases']==828")
 replace("counts['extra_whole_page_endpoint_relations']==4716 and counts['exact_format_IAT_endpoint_relations']==4716", "counts['extra_whole_page_endpoint_relations']==4968 and counts['exact_format_IAT_endpoint_relations']==4968")
 anchor="   for key,value in family_artifacts.items():"
 added="""   need(counts['widget_actual_root_phases']==42 and counts['widget_whole_source_page_endpoints']==114264 and counts['widget_whole_CRT_phase_page_endpoints']==105984 and counts['widget_whole_nonstack_carried_page_relations']==55896,'Complete actual138 whole69 source and64 CRT endpoints with same-branch nonstack chronology')
   need(counts['widget_complete_GDI_boundary_sides']>0 and counts['widget_actual_GetStockObject_calls']>0 and counts['widget_actual_CreateFontA_calls']>0 and counts['widget_complete_FPS_boundary_sides']>0 and counts['widget_actual_FPS_cdeclRET_relations']*2==counts['widget_complete_FPS_boundary_sides']and counts['widget_actual_FS_instruction_events']>0,'Genuine normal GDI/FPS/FS paths reached; all counts measured, no predicted API totals')
   for label,value in(('widget-GDI-observations',widget.events),('widget-FS-observations',widget.fs),('FPS-observations',widget.fps),('widget-root-observations',widget.phases),('whole-source-page-relations',widget.page_relations),('whole-registry-BEFORE',widget.registry),('font-resource-lifetimes',widget.lifetimes),('new-root-heap-observations',widget.allocations)):
    target=out/(label+'.json');target.write_text(json.dumps(value,indent=2)+'\\n');pin(target)
   need(not(STORAGE_ROOT/'reports/m4-startup138-original'/name/'paired-exports').exists(),'Fresh same-session raw equality export only');export=Export(STORAGE_ROOT/'reports/m4-startup138-original'/name/'paired-exports','original',transport,pin);export.copy(records);paired_exports.append(export.finish())
"""
 replace(anchor,added+anchor)
 replace("pin(Tool_mfc:=Path(__file__).resolve().parent/'mfc_phase_v3.py');pin(sys.executable);passed=True", "pin(ROOT/'tools/m4-startup131-original/mfc_phase_v3.py');pin(Path(__file__).resolve().parent/'widget_phase.py');pin(ROOT/'tools/m4-joint-startup131/paired_exports.py');pin(ROOT/'tools/analysis/pe.py');\n   for tool in('run_storage.py',):pin(ROOT/'tools/m4-crt-allocation-root'/tool)\n   for tool in('capture_bundle_storage.py','paths_capture_storage.py','stages_capture_storage.py','paths.py','manifests.py'):pin(ROOT/'tools/m4-pipeline'/tool)\n   pin(sys.executable);passed=True")
 replace("  finally:records.close()", "  finally:\n   if export is not None:export.close()\n   records.close()")
 replace("scope='Actual original131 six persistent relative-order sequences, genuine MSVCP50 loaded provider pages/state2/CS, 15 actual original Lockit/tree owners, normal FS and101callbackregistration schedule; no nativecredit'", "scope='Actual original138 six persistent relative-order sequences with every inherited131 observation check plus current GDI/FPS selectors, complete69source/64CRT inputs, actual font occurrences and108 literal callback schedule; independent literal and native proofs remain separate'")
 replace("original_capture=str(Path(execution)/'original/transport.json')", "original_capture=str(transport)if transport is not None else None,paired_exports=paired_exports,paired_export_readers_closed=True")
 replace("observed_pages=43,external_whole_pages=3,combined_pages=46,callbacks=101", "observed_pages=43,external_whole_pages=26,combined_pages=69,callbacks=108")
 replace("reader_scope='Only fresh original131 capture in one bounded session; all DirectSet handles closed in finally'", "reader_scope='Only fresh original138 canonical capture once, with same-session whole raw equality export on G; all DirectSet/export handles closed in finally',source_model_equivalence=False,full_reached_source_instruction_trace=False,source_shutdown_callbacks_executed=False,source_failure_unwind_admitted=False,manual_cleanup_is_source_callback=False,borrowed_stock_deleted_as_owned=False,initializer_credit=0")
 ast.parse(text);helper=pin(R/'tools/m4-startup138-original/widget_phase.py');ast.parse(helper.read_text())
 validator=R/'tools/m4-startup138-original/validate.py';need(not validator.exists(),'Additive validator source only');validator.write_text(text);pin(validator)
 for path in('tools/m4-startup131-original/mfc_phase_v3.py','tools/m4-tree-original/full_tree_phase.py','tools/m4-startup130-original/family_phase_v2.py','tools/m4-joint-startup131/paired_exports.py','tools/m4-crt-allocation-root/run_storage.py','tools/m4-pipeline/capture_bundle_storage.py','tools/m4-pipeline/paths_capture_storage.py','tools/m4-pipeline/stages_capture_storage.py','tools/m4-pipeline/paths.py','tools/m4-pipeline/manifests.py','tools/analysis/pe.py','reports/m4-fps-original/preparation-r1/normal-contracts.json','reports/m4-tree-review/original138-prelaunch-r5/compiled-observers.json','reports/m4-startup138-original/admitted-controller-r1/report.json','reports/m4-constructor-native/admitted-controller-r1/report.json'):
  pin(R/path)
 pin(__file__);pin(sys.executable);out.mkdir();delta=out/'validator-deltas.json';delta.write_text(json.dumps(changes,indent=2)+'\n');pin(delta);inventory=out/'page-order.json';inventory.write_text(json.dumps(dict(whole_source_pages=whole,fixed_pages=whole[:43],external_pages=whole[43:],source='physically compiled preparation7/spec.hpp'),indent=2)+'\n');pin(inventory)
 report=dict(passed=True,scope='Source-only additive original138 observation validator preparation; no capture or worker execution, no initializer credit',validator_path=str(validator),validator_sha256=sha(validator),helper_path=str(helper),helper_sha256=sha(helper),parent_validator_path=str(parent),parent_validator_sha256=sha(parent),explicit_additive_hunks=len(changes),preparation_path=str(prep/'report.json'),preparation_sha256=PREP,build_path=str(build),build_sha256=BUILD,prelaunch_path=str(review),prelaunch_sha256=REVIEW,source_review_sha256=SOURCE_REVIEW,semantic_schedule_roots=138,sequences=6,expected_root_phases=828,callbacks=108,fixed_record_bytes=356992,fixed_pages=43,external_pages=26,whole_source_pages=69,whole_CRT_pages=64,widget_FS_event_bytes=1224,inherited_FS_event_bytes=1216,expected_whole_source_page_endpoints=114264,expected_whole_CRT_page_endpoints=105984,expected_whole_nonstack_carried_page_relations=55896,actual_GDI_FPS_FS_counts_unmeasured=True,selector_effective_limit_requires_actual_descriptor=True,unclassified_new_allocations_retained=True,full_source_proof=False,source_shutdown_callbacks_executed=False,manual_cleanup_is_source_callback=False,original_executed=False,native_executed=False,capture_reader_opened=False,validation_executed=False,initializer_credit=0,planned_arguments=[str(build),BUILD,'CURRENT_EXECUTION_DIRECTORY',str(review),REVIEW,'FRESH_VALIDATION_NAME'],files=files)
 target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(target),sha256=sha(target),validator_sha256=sha(validator),helper_sha256=sha(helper),hunks=len(changes),pins=len(files))))
if __name__=='__main__':main(sys.argv[1])
