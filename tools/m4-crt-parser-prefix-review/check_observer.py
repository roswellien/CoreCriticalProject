"""Same rich hardware semantic controls through pinned archive logical reads."""
import json, pathlib, sys
sys.dont_write_bytecode=True
from transport import ROOT,T,need,opened,read_json,sha_file,verify_manifest,semantic_inventory
from review import dependencies,publication_stage
BASE=ROOT/'reports/m4-crt-parser-prefix'

def main(build_path,out):
 need(out.parent==BASE and out.name.startswith('independent-compiled-') and not out.exists(),'Fresh observer proof output');out.mkdir()
 build=read_json(build_path);need(build['passed'],'Successful compiled fixture required');files=dependencies(build)
 stage=publication_stage(build_path,build,files)
 from native_receipts import validate as native_receipts
 native_commands=native_receipts(build_path,build,files)
 for p in (build_path,pathlib.Path(__file__).absolute(),ROOT/'tools/m4-crt-parser-prefix-review/review.py'):T.add(files,p,sha_file(p))
 validator,association=T.load_validator();actual=0;inventory_tests=[]
 for level in ('O0','O2'):
  bundle,reader,result=opened(build,level)
  try:
   for i in range(1,67):
    for actor in ('writer','entry'):validator(reader.path(f'case-{i}/{actor}-host-before.bin'),reader.path(f'case-{i}/{actor}-host-after.bin'),i);actual+=1
   if level=='O0':
    before=reader.read_bytes('case-1/entry-host-before.bin');after=reader.read_bytes('case-1/entry-host-after.bin')
    class Overlay:
     def __init__(self,changes=None,names=None):self.changes=changes or {};self.inventory=names
     def read_bytes(self,name):return self.changes[name] if name in self.changes else bundle.read_bytes(name)
     def names(self):return self.inventory if self.inventory is not None else bundle.names()
    records=reader.expected
    def rejection(label,overlay):
     denied=False;reason=''
     try:semantic_inventory(overlay,records)
     except (ValueError,KeyError) as error:denied=True;reason=str(error)
     need(denied,'Independent inventory/request corruption must refuse');inventory_tests.append(dict(label=label,denied=True,reason=reason))
    rejection('missing_COMPLETE',Overlay({'COMPLETE':b'PARTIAL!'}))
    rejection('missing_case_record',Overlay(names=tuple(n for n in bundle.names() if n!='case-1/parser-events.bin')))
    rejection('extra_case_record',Overlay(names=tuple(sorted(bundle.names()+('case-67/parser-status.bin',)))))
    rejection('missing_required_locale_phase',Overlay(names=tuple(n for n in bundle.names() if n!='case-1/parser-locale-before/state.bin')))
    rejection('invented_locale_phase_on_early_fault',Overlay(names=tuple(sorted(bundle.names()+('case-19/parser-locale-before/state.bin',)))))
    rejection('wrong_independent_request',Overlay({'case-1/mainargs-mode.bin':(85).to_bytes(4,'little')}))
    status=bytearray(bundle.read_bytes('case-1/parser-status.bin'));status[32:36]=(1).to_bytes(4,'little');rejection('active_boundary_depth',Overlay({'case-1/parser-status.bin':bytes(status)}))
    status=bytearray(bundle.read_bytes('case-1/parser-status.bin'));status[48:52]=(1).to_bytes(4,'little');rejection('active_parser_after_cleanup',Overlay({'case-1/parser-status.bin':bytes(status)}))
    for field,value in (('passed',1),('scenarios',65),('original_executed',True),('ordinary_game_launched',True),('whole_M4_complete',True),('malformed_token_denials',26)):
     changed=dict(result);changed[field]=value;rejection('result_'+field,Overlay({'controls.json':json.dumps(changed).encode()}))
  finally:bundle.close()
 preservation=list(range(5))+list(range(24,28))+[32+16*i+k for i in range(8) for k in range(10)]+[160+16*i+k for i in range(6,16) for k in range(16)]+list(range(512,540))
 fixtures=list(range(5))+list(range(24,28))+[32+16*i+k for i in range(8) for k in range(10)]+[160+16*i+k for i in range(6,16) for k in range(16)]+[512,513,516,517,520,521]+list(range(524,538))
 tests=[]
 for direction,offsets in (('after',preservation),('coherent_wrong_before_fixture',fixtures)):
  for offset in offsets:
   b=bytearray(before);a=bytearray(after);a[offset]^=1
   if direction!='after':b[offset]^=1
   pb,pa=T.overlay_paths(b,a);denied=False;reason=''
   try:validator(pb,pa,1)
   except ValueError as error:denied=True;reason=str(error)
   need(denied,'Meaningful frozen validator field corruption rejected');tests.append(dict(direction=direction,offset=offset,denied=True,reason=reason))
 for extent in (543,545):
  pb,pa=T.overlay_paths(before[:extent] if extent<544 else before+b'\0',after);denied=False
  try:validator(pb,pa,1)
  except ValueError:denied=True
  need(denied,'Wrong hardware extent rejected');tests.append(dict(direction='wrong_extent',bytes=extent,denied=True))
 need(actual==264 and len(tests)==548,'Complete actual before fixtures and preserved semantic control domain')
 closure=verify_manifest(files)
 need(len(inventory_tests)==14,'Complete independent new case inventory/request control domain')
 report=dict(passed=True,publication_stage=stage,native_commands=native_commands,actual_hardware_raw80_before_fixtures=264,actual_complete_legacy_tag_before_fixtures=264,meaningful_corruption_denials=548,independent_inventory_request_denials=14,inventory_tests=inventory_tests,validator=association,archives=build['capture_archives'],closure=closure,tests=tests,files=files,new_native_executions=False,guest_result_inferred_from_AFTER=False,volatile_XMM0_5_equality_claimed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','actual_hardware_raw80_before_fixtures','meaningful_corruption_denials')}))

if __name__=='__main__':
 need(len(sys.argv)==3,'check_observer.py sealed-build.json fresh-output');main(pathlib.Path(sys.argv[1]).absolute(),pathlib.Path(sys.argv[2]).absolute())
