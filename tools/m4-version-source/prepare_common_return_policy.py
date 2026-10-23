"""Literal successful atexit return policy, exact inverse and finite CPU controls."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 parent=pin(R/'tools/m4-version-source/compare_common_v1.py','b46de35b4c118a17b5ef8c0f0722b1c910813ef0f48489c33d0c64660fd82c55');s=parent.read_text();old="after[0]==0x4af270,'Exact own source root caller/RET/registered callback'";new="after[0]==0,'Exact own source root caller/RET/successful literal atexit return'";assert s.count(old)==1;current=s.replace(old,new,1);assert current.replace(new,old,1)==s;ast.parse(current)
 graph=json.loads(pin(R/'reports/m4-remaining-service-source/preparation-r1/all-seven-graphs.json').read_bytes())[str(0x5ac140)]
 expected=[(0x5ac140,'8b442404'),(0x5ac144,'50'),(0x5ac145,'e8c6ffffff'),(0x5ac14a,'83c404'),(0x5ac14d,'f7d8'),(0x5ac14f,'1bc0'),(0x5ac151,'f7d8'),(0x5ac153,'48'),(0x5ac154,'c3')];assert [(v['pc'],v['bytes'])for v in graph['instructions']]==expected
 spec=importlib.util.spec_from_file_location('physical_pe',pin(R/'tools/analysis/pe.py'));pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe);image=pe.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 expected.extend([(0x4af240,'e80b000000'),(0x4af245,'e916000000'),(0x4af260,'6870f24a00'),(0x4af265,'e8d6ce0f00'),(0x4af26a,'83c404'),(0x4af26d,'c3')])
 physical=[]
 for pc,h in expected:
  b=bytes.fromhex(h);off,available=image.rva_range(pc-image.image_base,len(b));assert image.read(off,len(b))==b;physical.append(dict(pc=pc,bytes=h,file_offset=off))
 callback=0x4af270;neg=(-callback)&0xffffffff;carry=int(callback!=0);sbb=(-carry)&0xffffffff;neg2=(-sbb)&0xffffffff;returned=(neg2-1)&0xffffffff;assert returned==0
 # Both linked prelaunch source/object reviewer reports already authenticate these literal functions and actual wrapper linkage.
 for p,h in [('reports/m4-tree-review/version-original-common-prelaunch-r2/report.json','caa8b189a0da510dee164f3b54b51decd0d0662a110e77d5204f09adf1bf5f5d'),('reports/m4-tree-review/version-native-common-prelaunch-r1/report.json','c1d894005c1a3e6f3273d12e34e3716a0dcffc0b2176a014e25013c95b6f6938')]:assert json.loads(pin(R/p,h).read_bytes())['passed']
 service=pin(R/'reports/m4-version-source/service-preparation-r4/session_impl.inc').read_text();assert 's.gpr.rax.dword==callback' in service and 'load<unsigned>({next})==callback' in service
 q=R/'tools/m4-version-source/compare_common_v2.py';assert not q.exists();q.write_text(current);pin(q)
 spec=importlib.util.spec_from_file_location('exact_return_policy',q);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 diag=json.loads(pin(R/'reports/m4-version-source/common-cpu-diagnostic-r1/report.json','ee140752d80c47ace3f00f41fea98b3ba9e0308bed04382254b8975e30ae5895').read_bytes());assert diag['passed']and diag['reader_closed'];controls=[]
 for role,row in diag['rows'].items():
  ret=0x410a80 if role=='original'else 0xfffffff0;mod.own_endpoint(row['before'],row['after'],ret);controls.append(role+'-actual-fullCPU10-pass')
  for index,value in((0,callback),(9,0),(4,row['before'][4])):
   after=row['after'][:];after[index]=value
   try:mod.own_endpoint(row['before'],after,ret)
   except ValueError:controls.append(role+'-alteredCPU'+str(index)+'-refused')
   else:raise AssertionError('Exact changed full record must refuse')
 assert diag['rows']['original']['registration']==[callback]
 pin(__file__);pin(sys.executable)
 for p,h in pins.items():assert sha(p)==h
 r=dict(passed=True,scope='One exact successful literal atexit EAX return condition; physical source and exact CPU10 controls; no CPU masks',entrypoint=str(q),entrypoint_sha256=sha(q),parent_sha256=sha(parent),exact_inverse_restores_parent=True,all_other_comparison_gates_retained=True,source_callback_argument=callback,onexit_success_return=callback,atexit_literal_return=returned,measured_PC_preserved=True,physical_source_rows=physical,controls=controls,reader_admission_requires_current_comparator_hash=True,archive_reader_opened=False,worker_launched=False,source_original_equivalence=False,initializer_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),compare_sha256=sha(q),controls=controls)))
if __name__=='__main__':main(sys.argv[1])
