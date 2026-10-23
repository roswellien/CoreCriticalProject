"""Actual ordinary COFF TLS16 layout plus adverse ownership controls only."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024;v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h;pins[str(p)]=v;return p
 def load(p,name):
  spec=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 C=load(R/'tools/m4-tree-review/amd64_coff.py','physical_tls16_coff');T=load(R/'tools/m4-138-criteria-frontier/current_controls_tls16_v1.py','strict_current_TLS16')
 rp=pin(R/'reports/m4-tree-review/joint138-controls-prelaunch-r4/report.json','55990e0cff619c9ee69f2e5e81e27d9e6e92bd4da8d0b5557e4eb28879a10b3a');parent=json.loads(rp.read_bytes());rows=[];tests=[]
 for level in ('O0','O2'):
  p=R/f'reports/m4-joint-startup138/controls-build-r2/build-{level}/CMakeFiles/mw34_widget_context_controls.dir/controls_main.cpp.obj';sy,se=C.parse(pin(p,parent['files'][str(p)]).read_bytes());owners=[s for s in sy.values()if s['name']in('?observation@m4_mixed@mw34@@3PEAUNative@12@EA','?injection@context_control@@3PEAUInjection@1@EA')and s['section']>0];assert len(owners)==2
  for sym in owners:rows.append(dict(level=level,COFF=str(p),proof=T.prove(sym,se,sy,se)))
  sym=owners[1];section=sym['section']
  for label in ('offset','name','storage_class','nonzero','extra_owner','missing_observation','unrelated_sections','relocation'):
   symbols=copy.deepcopy(sy);sections=copy.deepcopy(se);input_sections=copy.deepcopy(se);symbol=copy.deepcopy(sym)
   if label=='offset':symbol['value']=0
   if label=='name':symbol['name']='unrelated-injection'
   if label=='storage_class':symbol['storage']=2
   if label=='nonzero':sections[section]['bytes']=b'\x01'+bytes(15);input_sections=copy.deepcopy(sections)
   if label=='extra_owner':symbols[max(symbols)+1]=dict(sym,name='extra-owner')
   if label=='missing_observation':symbols={k:v for k,v in symbols.items()if not v['name'].startswith('?observation@')}
   if label=='unrelated_sections':input_sections[section]['flags']^=1
   if label=='relocation':sections[section]['relocations']=[dict(offset=0,type=4,symbol=sym)];input_sections=copy.deepcopy(sections)
   rejected=False
   try:T.prove(symbol,input_sections,symbols,sections)
   except AssertionError:rejected=True
   assert rejected,(level,label);tests.append(dict(level=level,mutation=label,rejected=True))
 pin(R/'reports/m4-138-criteria-frontier/current-controls-prelaunch-preparation-r7/report.json','23e5294106768b5503099ff78c027823ceb0c5c265ed026ea4ebce629f0939e4');pin(__file__);pin(sys.executable);r=dict(passed=True,scope='Exact physically pinned current O0/O2 two-owner initialized TLS16 section; no runtime TLS/frame observation or full worker review',physical_owner_rows=rows,adverse_controls=tests,worker_executed=False,archive_reader_opened=False,fullphysical_reviewer_executed=False,allowance_created=False,accepted_function_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(r,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
