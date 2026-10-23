"""Exact immutable discriminated growth extension and bounded controls."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or v==h;PINS[str(p)]=v;return p
base=R/'reports/m4-joint-startup138-source/combined-source-provider-r6';report=json.loads(pin(base/'report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052').read_bytes())
def output(n):
 p=base/n;return json.loads(pin(p,report['files'][str(p.resolve())]).read_bytes())
rows=output('Widget-source-derivations.json');phases=output('phases.json');api=output('API-identity-proofs.json')['observations'];pm={(x['level'],x['sequence'],x['entry']):x for x in phases};pi={(x['level'],x['sequence'],x['phase']):x for x in phases};am={(x['level'],x['sequence'],x['API_index']):x for x in api}
def load(name,p):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
helper=R/'tools/m4-138-controls-review/widget_growth_contract.py';M=load('bounded_widget_growth_contract',helper);gp=R/'reports/m4-fps-original/source-preparation-r4/game_model.py';program,_=load('bounded_widget_physical_model',pin(gp,report['files'][str(gp.resolve())])).source_program()
interface=R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json';contracts=json.loads(pin(interface,report['files'][str(interface.resolve())]).read_bytes())
for d in contracts['instructions']:
 if d['pc']in program:assert program[d['pc']]['bytes_hex']==d['bytes_hex']and program[d['pc']]['width']==d['width']
 else:program[d['pc']]=d
pepath=R/'tools/analysis/pe.py';PE=load('bounded_widget_physical_PE',pin(pepath,report['files'][str(pepath.resolve())]));dll=R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';pe=PE.PEImage(pin(dll,report['files'][str(dll.resolve())]).read_bytes());pcs={pc for row in rows for pc,a,v,n,w in row['borrowed_provider']['provider_source_rows']}
for pc in pcs:
 d=program[pc];raw=bytes.fromhex(d['bytes_hex']);offset=pe.rva_range(pc-pe.image_base,len(raw))[0];assert pe.read(offset,len(raw))==raw
results=[];domains=[]
for row in rows:
 case=row['level'],row['sequence'];p=pm[case+(row['root'],)];a=pi[case+(p['phase']-1,)]['finite_API_index'];b=p['finite_API_index'];observed=[am[case+(i,)]for i in range(a,b)];proof=M.verify(row,observed,program);results.append(dict(level=case[0],sequence=case[1],root=row['root'],**proof));domains.append((row,observed))
controls=[]
for name,which,mutation in [('wrong capacity discriminates branch',3,lambda r,a:a[1]['witness_words'].__setitem__(8,a[1]['witness_words'][8]+4)),('wrong growth request denied',3,lambda r,a:a[3]['witness_words'].__setitem__(23,a[3]['witness_words'][23]+4)),('wrong physical source PC denied',0,lambda r,a:r['borrowed_provider']['provider_source_rows'][0].__setitem__(0,0x123456)),('missing provider operand denied',3,lambda r,a:r['borrowed_provider']['provider_source_rows'].pop()),('wrong callback publication denied',0,lambda r,a:next(v for v in r['borrowed_provider']['provider_source_rows']if v[0]==0x78004a67).__setitem__(2,1))]:
 row,observed=copy.deepcopy(domains[which]);mutation(row,observed)
 try:M.verify(row,observed,program)
 except(ValueError,KeyError):controls.append(dict(name=name,rejected=True))
 else:raise AssertionError(name)
old=R/'tools/m4-138-controls-review/review_source6_widgets.py';text=old.read_text();original=text;changes=[]
def one(a,b):
 global text
 assert text.count(a)==1;text=text.replace(a,b);changes.append(dict(before=a,after=b))
insertion="""  phases=output('phases.json');phase_map={(x['level'],x['sequence'],x['entry']):x for x in phases};phase_index={(x['level'],x['sequence'],x['phase']):x for x in phases};identities=output('API-identity-proofs.json')['observations'];API_map={(x['level'],x['sequence'],x['API_index']):x for x in identities}
  helper_path=pin(R/'tools/m4-138-controls-review/widget_growth_contract.py',HELPER_SHA);spec=importlib.util.spec_from_file_location('independent_literal_widget_growth',helper_path);WG=importlib.util.module_from_spec(spec);spec.loader.exec_module(WG)
  model_path=R/'reports/m4-fps-original/source-preparation-r4/game_model.py';spec=importlib.util.spec_from_file_location('independent_widget_program',pin(model_path,r['files'][str(model_path.resolve())]));GM=importlib.util.module_from_spec(spec);spec.loader.exec_module(GM);program,_=GM.source_program()
  contract_path=R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json';contract=read(contract_path,r['files'][str(contract_path.resolve())])
  for d in contract['instructions']:
   if d['pc']in program:need(program[d['pc']]['bytes_hex']==d['bytes_hex']and program[d['pc']]['width']==d['width'],'Exact retained/additional provider literal descriptor')
   else:program[d['pc']]=d
  for x in rows:
""".replace('HELPER_SHA',repr(sha(helper)))
one("  for x in rows:\n",insertion)
one("   need(len(b['provider_source_rows'])==67 and b['provider_source_end']-b['provider_source_start']==67 and b['provider_source_start']==b['provider_before_source_index']+2,'Exact complete borrowed67 operand interval')", "   case=x['level'],x['sequence'];phase=phase_map[case+(root,)];first=phase_index[case+(phase['phase']-1,)]['finite_API_index'];last=phase['finite_API_index'];growth=WG.verify(x,[API_map[case+(i,)]for i in range(first,last)],program);counts['physically_discriminated_growth_intervals']+=int(growth['growth'])\n   need(b['provider_source_end']-b['provider_source_start']==growth['expected_provider_operands'] and b['provider_source_start']==b['provider_before_source_index']+2,'Exact independently discriminated complete borrowed source interval')")
inverse=text
for c in reversed(changes):assert inverse.count(c['after'])==1;inverse=inverse.replace(c['after'],c['before'])
assert inverse==original;ast.parse(text);q=R/'tools/m4-138-controls-review/review_source6_widgets_v3.py';assert not q.exists();q.write_text(text)
out=R/'reports/m4-138-controls-review/source6-widget-growth-preparation-r1';assert not out.exists();out.mkdir(parents=True)
for p in(old,q,Path(__file__)):pin(p)
f=out/'report.json';result=dict(passed=True,scope='Exact literal typed HeapSize capacity/used-byte branch discriminator, repeated owning query and HeapReAlloc request/guestresult publications; all84 sealed ordinary source journals checked, physical borrowed instruction bytes freshly matched stagedCRT; no payload/archive or machine execution. Existing journal/physical identity predicates retained.',changes=changes,inverse_restores_entire_parent=True,bounded_growth_results=results,physical_source_operand_PCs=len(pcs),negative_controls=controls,reviewer_executed=False,capture_archives_opened=0,full_source_widget_acceptance_closed=False,initializer_credit=0,files=PINS);f.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(f),tool_sha256=sha(q),growth_intervals=sum(v['growth']for v in results))))
