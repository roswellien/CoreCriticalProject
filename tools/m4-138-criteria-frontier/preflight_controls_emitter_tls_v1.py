"""Actual current component TLS24 typed owner/source proof and adverses."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024;v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 def load(p,name):
  spec=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 C=load(R/'tools/m4-tree-review/amd64_coff.py','actualEmitterCOFF');E=load(R/'tools/m4-138-criteria-frontier/current_controls_emitter_tls_v1.py','exactEmitterTLS')
 p=pin(R/'reports/m4-tree-review/joint138-controls-prelaunch-r4/report.json','55990e0cff619c9ee69f2e5e81e27d9e6e92bd4da8d0b5557e4eb28879a10b3a');pr=json.loads(p.read_bytes());source_path=R/'reports/m4-joint-startup138/controls-preparation-r4/connected_component.cpp';source=pin(source_path,pr['files'][str(source_path)]).read_text();rows=[];tests=[]
 for level in ('O0','O2'):
  p=R/f'reports/m4-joint-startup138/controls-build-r2/build-{level}/CMakeFiles/mw34_widget_context_controls.dir/connected_component.cpp.obj';sy,se=C.parse(pin(p,pr['files'][str(p)]).read_bytes());symbols=[s for s in sy.values()if s['name']==E.NAME and s['section']>0];assert len(symbols)==1;sym=symbols[0];rows.append(dict(level=level,whole_COFF=str(p),proof=E.prove(sym,sy,se,source)))
  for label in ('wrong_namespace','wrong_offset','wrong_type','wrong_storage','nonzero','missing_owner','extra_owner','relocation','wrong_source_sink','wrong_source_threadlocal'):
   x=copy.deepcopy(sym);ys=copy.deepcopy(sy);zs=copy.deepcopy(se);src=source;section=sym['section']
   if label=='wrong_namespace':x['name']=x['name'].replace('CA9AC4E1','D25E2230')
   if label=='wrong_offset':x['value']=0
   if label=='wrong_type':x['type']=32
   if label=='wrong_storage':x['storage']=2
   if label=='nonzero':zs[section]['bytes']=bytes(23)+b'\x01'
   if label=='missing_owner':ys={k:v for k,v in ys.items()if not v['name'].startswith('?current@Impl@')}
   if label=='extra_owner':ys[max(ys)+1]=dict(sym,name='unrelated_alias')
   if label=='relocation':zs[section]['relocations']=[dict(offset=8,type=4,symbol=sym)]
   if label=='wrong_source_sink':src=src.replace('Sink sink{}','unsigned sink{}')
   if label=='wrong_source_threadlocal':src=src.replace('thread_local Emitter emitter{};','Emitter emitter{};')
   rejected=False
   try:E.prove(x,ys,zs,src)
   except AssertionError:rejected=True
   assert rejected,(level,label);tests.append(dict(level=level,mutation=label,rejected=True))
 pin(R/'reports/m4-138-criteria-frontier/current-controls-prelaunch-preparation-r9/report.json','d887e9bd1c6e42ae8a274ef88ede2fca312d654a1ac38560194b8b8a84eb1f9b');pin(__file__);pin(sys.executable);r=dict(passed=True,scope='Actual compiled current component source-declared Emitter TLS24 ownership/layout only; no runtime TLS observation or fullphysical review',actual_owners=rows,adverse_controls=tests,worker_executed=False,archive_reader_opened=False,physical_reviewer_executed=False,accepted_function_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(r,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
