"""Physical static caller superset and actual registrar branch predicate.
An unresolved static superset is not a claim of all original CPU execution.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def module(n,p):
  spec=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 PE=module('physical',R/'tools/analysis/pe.py');D=module('ordinary',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');gp=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');gate=json.loads(gp.read_bytes());assert gate['passed']and gate['reader_closed'];prep=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161').read_bytes());graphs=json.loads(pin(R/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json').read_bytes());roots=[r['entry']for r in prep['selected_order']];seen=set();todo=roots[:]
 while todo:
  a=todo.pop()
  if a in seen:continue
  seen.add(a);assert str(a)in graphs;todo.extend(r['target']for r in graphs[str(a)]['direct_calls'])
 assert len(roots)==138 and len(seen)==314
 imports={};unresolved=[];absolute_CRT=[]
 for a in sorted(seen):
  graph=graphs[str(a)]
  for r in graph['import_sites']:imports[r['site']]=r
  for r in graph['unresolved_controls']:unresolved.append(dict(graph_entry=a,**r))
  for r in graph['absolute_memory_references']:
   if 0x78035000<=r['address']<0x78038000:absolute_CRT.append(dict(graph_entry=a,**r))
 assert not absolute_CRT
 CRT={r['site']:r for r in imports.values()if r['symbol']['library'].lower()=='msvcrt.dll'};names={r['symbol']['name']for r in CRT.values()};assert names=={'_strdup','strrchr','malloc','sprintf','vsprintf','_onexit','__dllonexit','_setmbcp'}
 assert graphs[str(0x5ac110)]['instructions'][0]['bytes']=='833df0179a00ff'and graphs[str(0x5ac110)]['instructions'][1]['bytes']=='750f';assert CRT[0x5ac11e]['symbol']['name']=='_onexit'and CRT[0x5ac580]['symbol']['name']=='__dllonexit'
 e=next(e for e in gate['paired_exports']if e['branch']=='original');idx=pin(e['index_path'],e['index_sha256']);payload=pin(e['payload_path'],e['payload_sha256']);entries=D.entries(idx,re.compile(r'phase/[0-5]/\d+\.bin'));assert len(entries)==828;offset=prep['observed_pages'].index(0x9a1000)*4096+0x7f0;predicates=[]
 with payload.open('rb')as f:
  for seq in range(6):
   for phase in range(138):
    z=entries[f'phase/{seq}/{phase}.bin'];assert z['bytes']==356992;f.seek(z['offset']);b=f.read(z['bytes']);assert hashlib.sha256(b).hexdigest()==z['sha256'];a=struct.unpack_from('<I',b,2276+offset)[0];c=struct.unpack_from('<I',b,178404+offset)[0];assert a==c==0xffffffff;predicates.append(dict(sequence=seq,phase=phase,own_before=a,own_after=c,selected_BRANCH_5AC117_taken=False))
 strings=json.loads(pin(R/'reports/m4-strings-review/interface-r2/instruction-contracts.json').read_bytes());crt=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());assert len(strings['instructions'])==117;indirect=[]
 for row in strings['instructions']:
  raw=bytes.fromhex(row['bytes_hex']);off,_=crt.rva_range(row['pc']-crt.image_base,len(raw));assert crt.data[off:off+len(raw)]==raw
  for operand in row['decoded_operands']:
   if operand['kind']=='memory':
    assert operand['terms']or not 0x78035000<=operand['displacement']<0x78038000
    if operand['terms']and any(t['register']not in('esp','ebp')for t in operand['terms']):indirect.append(dict(PC=row['pc'],operand=operand))
 for r in strings['inputs']:assert r['physical_read_end']<=0x78035000 or r['source']>=0x78038000
 assert sha(idx)==e['index_sha256']and sha(payload)==e['payload_sha256'];cp=out/'callers.json';cp.write_text(json.dumps(dict(selected_roots=roots,static_direct_call_superset=sorted(seen),CRT_import_sites=list(CRT.values()),unresolved_static_superset=unresolved,actual_registrar_predicates=predicates,additional117_physical_string_indirect_roles=indirect),indent=2)+'\n');pin(cp);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Archive-free exact current registrar branch predicate at828 own phases; complete314direct-call static superset catalog and117physical string instructions with no absolute CRTdata operands. Indirect string roles require retained actual source input/owner proofs; unselected static alternate/virtual branches are not labeled executed.',own_registrar_branch_predicates=828,selected_roots=138,static_direct_call_superset=314,physical_additional_string_instructions=117,MSVCRT_import_names=sorted(names),unresolved_static_superset_graphs=len({r['graph_entry']for r in unresolved}),dllonexit_alternate_excluded_by_own_input=True,provider_full_CPU_executed=False,complete_selected138_original_provider_caller_closure_reviewed=False,complete_paired_policy_admitted=False,archive_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
