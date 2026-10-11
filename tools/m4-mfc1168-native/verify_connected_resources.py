"""Fresh current-Context real TLS/CS/API ownership and caller boundary gate.

The inherited physical PE checker is used as a read-only function library.
Canonical observations are read by their authenticated logical names; physical
system files are still freshly rehashed and exports/relocations reconstructed.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def eq(a,b,s):need(a==b,s+' '+str((a,b))[:550])
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical input');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(execution,digest,source,source_sha,name):
 out=R/'reports/m4-mfc1168-native'/name;need(not out.exists(),'Fresh current connected resource verification');out.mkdir();passed=False;closed=True;counts=collections.Counter();cases=[];proofs={};identities=[]
 try:
  e=read(execution,digest);need(e['passed']and e['all_workers_terminal']and e['all_bounded_readers_closed'],'Current actual workers terminal');s=read(source,source_sha);need(s['passed']and s['execution_sha256']==digest,'Complete current BEFORE-only source joins');b=read(e['build'],e['build_sha256']);p=read(b['preparation'],b['preparation_sha256'])
  for q,h in b['files'].items():pin(q,h)
  V=load(R/'tools/m4-mfc1168-native/verify_resource_fixture.py','mfc_connected_physical_exports');DS=load(R/'tools/m4-crt-allocation-root/run_v2.py','mfc_connected_actual_resources');V.PINS=PINS
  for level in('O0','O2'):
   row=next(x for x in e['levels']if x['level']==level);records=DS.DirectSet(Path(row['capture']),pin);closed=False
   try:
    stem='sequence-0/MFC/';virtual=(out/('logical-'+level)).resolve();oldraw=V.raw
    def resource_raw(path):
     path=Path(path).resolve()
     if path.is_relative_to(virtual):return records.data(stem+path.relative_to(virtual).as_posix())
     return oldraw(path)
    V.raw=resource_raw
    context=records.words(stem+'cleaned/resource-context.bin',12,'Q');eq(context[2:9],(0,0,0,0,0,113,4),'Exact actual native resources terminal and source extent');serials=context[11];eq(serials,13,'Exact current component thirteen actual service invocations');tls=None;association=0;section=None;depth=0;deleted=False;freed=False;thread=None;events=[]
    for serial in range(serials):
     base=virtual/'resources'/str(serial);words=struct.unpack('<8Q',resource_raw(base/'call.bin'));eq(words[:2],(1,serial),'Every actual named call contiguous physical serial');kind,arg0,arg1,result,tid,error=words[2:];need(kind<9,'Finite actual resource provider');thread=tid if thread is None else thread;eq(tid,thread,'One actual native current thread owns entire lifetime');identity=V.native_identity(base,kind,proofs);before=resource_raw(base/'CS-before40.bin');after=resource_raw(base/'CS-after40.bin');eq(len(before),40,'Complete actual native CS40 BEFORE');eq(len(after),40,'Complete actual native CS40 AFTER')
     if kind==0:need(tls is None and result!=0xffffffff,'One actual successful TLS slot');tls=result
     elif kind==1:eq(arg0,tls,'Actual owned TLS set index');need(not freed and result==1,'Actual TLS association set succeeds');association=arg1
     elif kind==2:eq(arg0,tls,'Actual owned TLS lookup index');need(not freed,'Actual lookup in live lifetime');eq(result,association,'Actual lookup equals current native mirror/NULL association')
     elif kind==3:eq(arg0,tls,'Exact owned TLS release index');need(not freed and not association and result==1,'Actual TLS clear before own release');freed=True
     elif kind==4:need(section is None,'One owned native CS40 construction');section=arg0;eq(V.cs(after),(0,0),'Actual initialized unheld native CS40')
     elif kind in(5,6):eq(arg0,section,'Actual owned native CS40 object identity');need(not deleted,'Live native CS operation');eq(V.cs(before),(depth,thread if depth else 0),'Actual hostCS40 incoming depth/thread');depth+=1 if kind==5 else -1;need(depth in(0,1),'Finite balanced actual native depth');eq(V.cs(after),(depth,thread if depth else 0),'Actual hostCS40 outgoing depth/thread')
     elif kind==7:eq(arg0,section,'Actual same owned CS40 deletion');need(not deleted and not depth,'Actual unheld native CS40 release');deleted=True
     elif kind==8:eq(result,1252,'Actual finite native ACP1252');need(depth==1 and not deleted,'Actual ACP query protected by same native codepage lock')
     events.append(dict(serial=serial,service=V.NAMES[kind],words=words,CS_before_hex=before.hex(),CS_after_hex=after.hex()));identities.append(dict(level=level,serial=serial,kind=kind,call_words=words,proof_identity=[kind,identity['actual_owner'],identity['RVA'],identity['entry64']]));counts['whole_actual_API_identity_and_CS40_sides']+=2
    eq([x['words'][2]for x in events],[0,2,1,4,2,5,8,6,2,7,1,2,3],'Exact compiled connected component normal service/lifecycle order');need(freed and deleted and not depth,'All actual TLS/CS40 resources released');counts['complete_actual_TLS_CS40_lifecycles']+=1
    eq(records.words(stem+'lifecycle.bin',8,'Q'),(1,thread,tls,4,0,1,1,1),'Complete actual caller-owned source/resource release receipt');hardware=records.data('sequence-0/MFC-caller-hardware.bin');eq(len(hardware),1632,'Entire actual caller three hardware sides');eq(hardware[:512],hardware[1088:1600],'Whole actual connected caller hardwareFX512 restored');eq(hardware[512:540],hardware[1600:1628],'Whole actual connected caller hardwareENV28 restored');counts['whole_connected_caller_hardwareFX512_ENV28']+=1
    cases.append(dict(level=level,actual_resource_services=events,whole_caller_hardware_hex=hardware.hex(),complete_TLS_CS40_cleanup=True,caller_scope='Assembly current14 selected-table invocation including MFC resource construction/source/release; old registry construction and cleanup outside',connected_refusal_cases_in_this_fixture=0))
   finally:V.raw=oldraw;records.close();del records;closed=True
  for filename,value in [('actual-provider-identity-joins.json',identities),('unique-physical-API-proofs.json',list(proofs.values())),('actual-current-lifecycle-caller.json',cases)]:target=out/filename;target.write_text(json.dumps(value,indent=2)+'\n');pin(target)
  pin(__file__);pin(sys.executable)
  for q,h in PINS.items():eq(sha(q),h,'Every successful physical input stable after reader closure')
  counts['unique_named_actual_physical_proofs']=len(proofs);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual current Context O0/O2 nine named physical native API owners/exports/executable/relocated entry64, complete TLS/CS40 source/lifetime and whole current caller hardware512/ENV28; no connected refusal or131 acceptance credit',execution=str(execution),execution_sha256=digest,source_comparison=str(source),source_comparison_sha256=source_sha,counts=dict(counts),files=PINS,all_bounded_readers_closed=closed,initializer_credit=0,source_AFTER_seed=False,connected_refusal_cases=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
