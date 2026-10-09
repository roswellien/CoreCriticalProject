"""NEW parser fixture inventory, using the frozen strict archive transport."""
import hashlib, importlib.util, json, pathlib, struct, sys
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).absolute().parents[2]
PINS = {
 'tools/m4-review-bundles/transport.py':'0feb19971049f6547dc40cdad1f338142d48de4bc8de4f675f2d71b2bc3f619f',
 'tools/m4-pipeline/capture_bundle.py':'486ec0074d1a7e5171f7744dc23cd5b0acb5b1e104242e58749ae77ccb79f4e1',
 'tools/m4-pipeline/paths.py':'c17b154b5dc86074d4df85f64108fe2cc587dbe8dacc3f303bf1b4f4d865ef66',
 'tools/m4-pipeline/manifests.py':'67b56e5622a1d3dd1b0cbf4d6eb5de5a71a773f01ac2cf584ea5f97a03a4dd9b'}
for relative, digest in PINS.items():
 if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen transport changed: '+relative)
spec=importlib.util.spec_from_file_location('frozen_parser_review_transport',ROOT/'tools/m4-review-bundles/transport.py')
T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T)
from capture_bundle import CaptureBundle, pack_capture, sha_file
from paths import publish_bytes, workspace_path
from manifests import unique_object, verify_manifest

def need(ok,why):
 if not ok:raise ValueError(why)

ANCESTOR_PHASES=set('commandline-api-after commandline-api-before commandline-buffer-after commandline-carry-after commandline-consumer-before commandline-parser-before commandline-producer-after commandline-producer-before commandline-producer-projected control-after control-before control-projected control-provider-after control-provider-before control-provider-projected entry-projected filename-api-after filename-before filename-buffer-after filename-commandline-before filename-return-after independent-after initterm-after initterm-before initterm-projected initterm-thunk-after initterm-thunk-before initterm-thunk-projected mainargs-after mainargs-before mainargs-builder-after mainargs-builder-before mainargs-builder-projected mainargs-projected matherr-after matherr-before matherr-projected'.split())
BEFORE_OWNED=set('commandline-api-after commandline-api-before commandline-producer-before commandline-producer-projected control-after control-before control-projected control-provider-after control-provider-before control-provider-projected entry-projected initterm-after initterm-before initterm-projected initterm-thunk-after initterm-thunk-before initterm-thunk-projected mainargs-before matherr-after matherr-before matherr-projected independent-after'.split())
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000)
PHASE_FILES=set('commandline-source.bin control-cold.bin control-hot.bin control-thunk.bin control-wrapper.bin crt-globals.bin entry-source.bin fx.bin initterm-provider.bin initterm-thunk.bin mainargs-builder.bin mainargs-provider.bin matherr-source.bin parser-source.bin runtime-cpu.bin state-cpu.bin state.bin tib-0.bin tib-24.bin tib-4.bin'.split())|{f'page-{p}.bin' for p in PAGES}
CASE_FILES=set('actual-filename-witness.bin calls.json carry-accesses.bin carry-actual-bytes.bin carry-consumer-accesses.bin carry-events.bin carry-status.bin entry-host-after.bin entry-host-before.bin filename-api-after.bin filename-api-before.bin filename-module-after.bin filename-module-before.bin filename-status.bin filename-witness.bin job-fault.bin mainargs-accesses.bin mainargs-events.bin mainargs-mode.bin mainargs-reason.txt mainargs-status.bin writer-host-after.bin writer-host-before.bin parser-accesses.bin parser-events.bin parser-undefined-sites.bin parser-status.bin'.split())
REQUESTS=[0]*6+list(range(85,97))+list(range(1,49))
LOCALE_MODES={0,3,4,18,19,20,21,22,23,24,94,95,96}
PARENT_ONLY_FAILURE_MODES=set(range(31,42))|{29,43,92}

def semantic_inventory(reader,records):
 need(reader.read_bytes('COMPLETE')==b'COMPLETE','Closed native writer COMPLETE marker')
 result=json.loads(reader.read_bytes('controls.json'),object_pairs_hook=unique_object)
 need(type(result['passed']) is bool and result['passed'] and type(result['scenarios']) is int and result['scenarios']==66 and result['original_executed'] is False and result['ordinary_game_launched'] is False and result['whole_M4_complete'] is False,'Exact requested fixture domain')
 need(type(result['checks']) is int and result['checks']>0 and type(result['malformed_token_denials']) is int and result['malformed_token_denials']==27,'Exact actual assertion and typed-token corpus')
 expected={'COMPLETE','controls.json'}
 for number,mode in enumerate(REQUESTS,1):
  case=f'case-{number}'
  need(struct.unpack('<I',reader.read_bytes(case+'/mainargs-mode.bin'))[0]==mode,'Independent fixed per-case request order')
  status=struct.unpack('<16I',reader.read_bytes(case+'/parser-status.bin'))
  need(status[0]==mode and status[1]==(mode if mode>=85 else int(mode==7)) and status[2]==0x2000182c+int(mode==5) and status[3]==0x20001860+int(mode==6) and status[7]==4 and status[8]==0 and status[11]==1 and status[12]==0 and status[13]==int(mode not in PARENT_ONLY_FAILURE_MODES) and status[14] in (0,1) and status[15]==0,'Actual parser case identity and terminal cleanup; parent-only token refusal does not invent a parser diagnostic')
  phases=ANCESTOR_PHASES|{'parser-before','parser-projected','parser-after'}
  if mode in LOCALE_MODES:phases=phases|{'parser-locale-before'}
  expected|={case+'/'+name for name in CASE_FILES}
  for phase in phases:
   expected|={case+'/'+phase+'/'+name for name in PHASE_FILES}
   if phase not in BEFORE_OWNED:expected.add(case+'/'+phase+'/commandline-owned.bin')
 need(reader.names()==tuple(sorted(expected)),'Exact independently specified case/phase/record inventory; no missing or extra evidence')
 T.validate_inventory(reader,records)
 return result,len(expected)

def read_json(path):return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def opened(build,level):
 info=build['capture_archives'][level]
 need(sha_file(info['inventory_path'])==info['inventory_sha256'],'Exact external logical inventory association')
 records=read_json(info['inventory_path'])['files']
 bundle=CaptureBundle(info['path'],info['sha256'])
 try:
  result,count=semantic_inventory(bundle,records)
  need(count==info['logical_files'],'Exact archive logical count')
  return bundle,T.LogicalReader(records,bundle=bundle),result
 except BaseException:bundle.close();raise
