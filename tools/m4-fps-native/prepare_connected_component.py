"""Sort only the exact seven root bindings and add a carried Context fault boundary.

The current58 literal programs and all per-root causal/GDI/FS/virtual slices are
unchanged. No candidate is executed, and isolated007f/TOP0 evidence is not
projected onto the connected six-case domain.
"""
from pathlib import Path
import hashlib,json,re,shutil,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(t,a,b):need(t.count(a)==1,'Unique exact additive source hunk');return t.replace(a,b)
def main(name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh connected component revision');out.mkdir();pins={};copies=[];changes=[];passed=False;report={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary inputs only');v=sha(p);need(h is None or v==h,'Exact input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def write(p,b):p.write_bytes(b if isinstance(b,bytes)else b.encode())
 try:
  pp=pin(R/'reports/m4-fps-native/component-preparation-r1/report.json','294ac018294dbb35b341d8c86e195d23b68ce0f249fa86aa02781e8c181c5a18');parent=read(pp);need(parent['passed']and parent['literal_bodies']==58,'Exact executed58 component source')
  ep=read(R/'reports/m4-fps-native/fixture-execution-r2/report.json','cfdcce62777df1f69c3ae15cfa1750dfde4e10ba28a83dfabbcdfb5656e77180');need(ep['passed'],'Passed isolated current seven')
  for label,digest in [('source-prefix-r1','545304f54cdef712f9dfd44bf3b9384ff9769ad5bd722d77c6c8cad890db1486'),('source-registry-r1','61949af6d50123ba09402a8eb07e96c62b6fdf34f61d6e379c96eaca427150af')]:need(read(R/'reports/m4-fps-native'/label/'report.json',digest)['passed'],'Exact own-BEFORE source prerequisite')
  for p,h in parent['files'].items():pin(p,h)
  for p in pp.parent.iterdir():
   if not p.is_file()or p.name=='report.json':continue
   q=out/p.name;shutil.copyfile(pin(p),q);copies.append(dict(name=p.name,source=str(p.resolve()),source_sha256=sha(p),target=str(q.resolve()),initial_copy_sha256=sha(q)))
  contract=json.loads((out/'contracts.json').read_bytes());prior_roots=contract['roots'];sorted_roots=sorted(prior_roots,key=lambda x:x['slot']);need([r['root']for r in sorted_roots]==[0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0],'Actual physical table order')
  plan=read(R/'reports/m4-fps-native/connected-phase-plan-r1/report.json','60160e0f346ad7490cbdea65124b4a0f73dfff23d0c415b1ec974c1d3fce1d1a')
  h=(out/'literals.hpp').read_text();a=h.index('inline constexpr Root roots[]{');b=h.index('\n};',a);part=h[a:b];rows=re.findall(r'^\{(\d+),[^\n]+',part,re.M);need(len(rows)==7,'Exact seven generated root header rows');lines=part.splitlines();headers={int(line.split(',')[0][1:]):line for line in lines[1:]};need(set(headers)=={r['root']for r in prior_roots},'Exact binding inventory')
  newpart=lines[0]+'\n'+'\n'.join(headers[r['root']]for r in sorted_roots);new=h[:a]+newpart+h[b:];write(out/'literals.hpp',new);changes.append(dict(name='literals.hpp',relation='Only whole seven Root header row order changes; each original row and all operand/provider slice arrays unchanged',before_sha256=sha(pp.parent/'literals.hpp'),after_sha256=sha(out/'literals.hpp')))
  contract['roots']=sorted_roots;contract['registration_epilogues']=sorted(contract['registration_epilogues'],key=lambda x:next(r['slot']for r in sorted_roots if r['root']==x['root']));contract['connected_root_slice_associations']=[dict(root=r['root'],slot=r['slot'],connected_component_index=i,isolated_component_index=next(j for j,x in enumerate(prior_roots)if x['root']==r['root']),whole_header=headers[r['root']])for i,r in enumerate(sorted_roots)];contract['connected_current_CW_TOP_route']=True;contract['per_root_State_or_FX_reseed']=False
  write(out/'contracts.json',json.dumps(contract,indent=2)+'\n')
  cpp=(out/'component.cpp').read_text();cpp=one(cpp,'static void entry(Runtime&r,unsigned root){require(current&&&current->r==&r,"Exact registered widget callback/owned current Runtime");current->invoke(root);}','static void entry(Runtime&r,unsigned root){require(current&&&current->r==&r,"Exact registered widget callback/owned current Runtime");try{current->invoke(root);}catch(...){current->failed=true;throw;}}')
  cpp=one(cpp,'void cleanup(){authority();require((!active||failed)&&!cleaned,"Serial explicit owned-font cleanup");','void cleanup(){require(current==this&&GetCurrentThreadId()==thread&&&services.runtime()==&r,"Current owned widget cleanup thread/Runtime");services.cleanup_authority();require((!active||failed)&&!cleaned&&(!r.poisoned()||failed),"Serial explicit owned-font cleanup after Context fault mark");')
  anchor='void Component::authority()';idx=cpp.find(anchor);need(idx>=0,'Existing public authority definition');end=cpp.index('\n',idx);cpp=cpp[:end+1]+'void Component::context_fault(){require(current==impl_.get()&&GetCurrentThreadId()==impl_->thread,"Actual carried Context fault owner");impl_->failed=true;}\n'+cpp[end+1:];write(out/'component.cpp',cpp)
  header=(out/'component.hpp').read_text();header=one(header,'  virtual void authority() = 0;','  virtual void authority() = 0;\n  // Manual owned-font cleanup may follow the same Context fault; no source API.\n  virtual void cleanup_authority() { authority(); }');header=one(header,'  void authority();','  void authority();\n  // Called by the owning connected Context before any post-fault font cleanup.\n  void context_fault();');write(out/'component.hpp',header)
  for name_ in ('component.cpp','component.hpp','contracts.json'):changes.append(dict(name=name_,before_sha256=sha(pp.parent/name_),after_sha256=sha(out/name_)))
  for row in copies:
   row['current_sha256']=sha(row['target']);row['byte_identical']=row['source_sha256']==row['current_sha256'];need(row['byte_identical']or row['name']in {r['name']for r in changes},'Only declared generated changes')
  # Exact whole slice hashes, including causal operand array bytes, persist.
  oldh=(pp.parent/'literals.hpp').read_text();need(oldh[:a]==new[:a]and oldh[b:]==new[b:],'Only root header block changes')
  irs=[str((out/Path(p).name).resolve())for p in parent['IRs']];need(len(irs)==58 and all(sha(p)==sha(pp.parent/Path(p).name)for p in irs),'All58 whole IRs byte-identical')
  relations=[dict(x,component_IR=str((out/Path(x['component_IR']).name).resolve()),component_sha256=sha(out/Path(x['component_IR']).name))for x in parent['namespace_relations']]
  for q in out.iterdir():
   if q.is_file():pin(q)
  pin(__file__);pin(sys.executable);passed=True
  report=dict(parent,roots=[r['root']for r in sorted_roots],IRs=irs,namespace_relations=relations,connected_CW_TOP_cases=[[0,127,0],[0,895,7],[0,3967,0],[1,1151,7],[1,2687,0],[1,3711,7]])
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report.update(passed=passed,scope='Unexecuted sorted seven-root connected component: exact whole per-root slices retained, current carried caller State/CW/TOP and explicit Context fault mark before manual owned-font cleanup',parent_component_preparation_sha256='294ac018294dbb35b341d8c86e195d23b68ce0f249fa86aa02781e8c181c5a18',prior_copy_relations=copies,changed_generated_files=changes,files=pins,native_executed=False,initializer_credit=0,connected_equivalence=False,source_native_equivalence=False,current_fault_evidence_pending=True)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
