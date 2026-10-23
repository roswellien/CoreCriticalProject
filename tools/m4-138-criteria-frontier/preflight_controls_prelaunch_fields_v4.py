"""Bounded source inverses and adverse controls; never runs physical reviewer."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024;v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 folder=R/'reports/m4-138-criteria-frontier/current-controls-prelaunch-preparation-r7';p=pin(folder/'report.json','23e5294106768b5503099ff78c027823ceb0c5c265ed026ea4ebce629f0939e4');pr=json.loads(p.read_bytes());assert pr['passed']is True
 delta=json.loads(pin(folder/'source-delta.json',pr['files'][str(folder/'source-delta.json')]).read_bytes());inverses=[]
 for row in delta:
  p=pin(folder/row['file'],row['current_sha256']);s=p.read_text()
  for edit in reversed(row['inverse_recipe']):
   if 'appended'in edit:assert s.endswith(edit['appended']);s=s[:-len(edit['appended'])]
   elif 'all_occurrences'in edit:assert s.count(edit['new'])==edit['all_occurrences'];s=s.replace(edit['new'],edit['old'])
   else:assert s.count(edit['new'])==1;s=s.replace(edit['new'],edit['old'])
  parent=pin(row['parent'],row['parent_sha256']);assert s==parent.read_text();inverses.append(row['file'])
 spec=importlib.util.spec_from_file_location('source8',pin(R/'tools/m4-138-criteria-frontier/current_controls_source_domains_v1.py'));S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
 positive=pin(R/'reports/m4-joint-startup138/preparation-r4/native_main.cpp').read_text();current=pin(R/'reports/m4-joint-startup138/controls-preparation-r4/native_main.cpp').read_text();controls=pin(R/'reports/m4-joint-startup138/controls-preparation-r4/controls_main.cpp').read_text();facts=S.prove(positive,current,controls);tests=[]
 for token in ['if(phase!=135)return','c.completed==135','mode>=1&&mode<=8','context.completed==135&&records.size()==135','first==context.failure_reason()','address=0x5bb52c','address=0x5a3ff0','address=0x736130','address=region=0x20001000','address=region=r.fs_base().value','c.control_route_override=1','s.addr.ds_base.dword=after','s.aflag.df=1','retry-before/Registry/','retry-after/Registry/','cleaned/Registry/']:
  assert token in controls;x=controls.replace(token,'BROKEN_TOKEN');rejected=False
  try:S.prove(positive,current,x)
  except AssertionError:rejected=True
  assert rejected;tests.append(dict(source_mutation=token,rejected=True))
 # Concrete aggregate: both85B bodies, source relocations and full unwind rows.
 p=pin(R/'tools/m4-tree-review/amd64_coff.py');spec=importlib.util.spec_from_file_location('coff8',p);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
 obj=pin(R/'reports/m4-joint-startup138/controls-build-r2/connected_hardware_boundary.obj','c0278517e21571c2a46ea0bf5ccb0ab659ff4a75ff30bbaf339b17127bcc39b4');sy,se=C.parse(obj.read_bytes())
 expected=bytes.fromhex('534883ec204889d3480fae03d9b300020000d9a300020000e800000000480fae8320020000d9b320040000d9a320040000480fae0bd9a300020000480fae8340040000d9b340060000d9a3400600004883c4205bc3')
 def aggregate(se):
  assert se[1]['bytes']==expected*2
  assert [(r['offset'],r['type'],r['symbol']['name'])for r in se[1]['relocations']]==[(25,4,'mfc_connected_invoke_guarded'),(110,4,'context_controls_guarded')]
  assert se[4]['bytes']==bytes.fromhex('01050200053201300105020005320130') and se[5]['bytes']==bytes.fromhex('00000000550000000000000055000000aa00000008000000')
 aggregate(se)
 for key,index in [(1,0),(1,85),(4,0),(4,8),(5,0),(5,12)]:
  x=copy.deepcopy(se);b=bytearray(x[key]['bytes']);b[index]^=1;x[key]['bytes']=bytes(b);rejected=False
  try:aggregate(x)
  except AssertionError:rejected=True
  assert rejected;tests.append(dict(aggregate_section=key,byte=index,rejected=True))
 for idx in (0,1):
  x=copy.deepcopy(se);x[1]['relocations'][idx]['offset']+=1;rejected=False
  try:aggregate(x)
  except AssertionError:rejected=True
  assert rejected;tests.append(dict(call_relocation=idx,rejected=True))
 p=pin(R/'tools/m4-138-criteria-frontier/current_control_target_join_v1.py',pr['files'][str(R/'tools/m4-138-criteria-frontier/current_control_target_join_v1.py')]);spec=importlib.util.spec_from_file_location('typed8',p);T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T)
 import struct
 for kind in range(4,10):
  raw=b'\xe8'+bytes(4)+b'\xc3';address=0x100000;target=0x101000;actual=b'\xe8'+struct.pack('<i',target-address-5-(kind-4))+b'\xc3';row=dict(offset=1,type=kind)
  proof=T.join(address,raw,actual,row,target);assert proof['target_address']==target and proof['CALL_opcode']is True
  tests.append(dict(typed_REL32=kind,positive=True))
  for label,args in [('wrong_target',(address,raw,actual,row,target+1)),('wrong_actual_call',(address,raw,b'\xe8'+struct.pack('<i',target-address-4-(kind-4))+b'\xc3',row,target)),('wrong_kind',(address,raw,actual,dict(offset=1,type=3),target))]:
   rejected=False
   try:T.join(*args)
   except AssertionError:rejected=True
   assert rejected;tests.append(dict(typed_REL32=kind,mutation=label,rejected=True))
 pin(folder/'review.py',pr['files'][str(folder/'review.py')]);pin(__file__);pin(sys.executable);r=dict(passed=True,scope='Whole five-block source inverse plus24 source/aggregate adverses and6positive18adverse typed target controls; not actual current8 linked reviewer execution',inverted_blocks=inverses,source_positive=facts,adverses=tests,physical_reviewer_executed=False,worker_executed=False,archive_reader_opened=False,allowance_created=False,accepted_function_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(r,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
