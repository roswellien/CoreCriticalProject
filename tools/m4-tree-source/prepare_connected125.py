"""Prepare additive strict125 adapters; accepted124 programs remain frozen."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PINS={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):p=ROOT/p;PINS[str(p)]=sha(p);return p.read_text()
def replace(s,a,b):
 if a not in s:raise ValueError('Missing exact adapter anchor '+a[:180])
 return s.replace(a,b)
def save(name,s):
 p=HERE/name
 if p.exists():raise ValueError('Fresh adapter '+str(p))
 ast.parse(s);p.write_text(s);PINS[str(p)]=sha(p)
def main():
 out=ROOT/'reports/m4-tree-source/connected125-preparation-r1'
 if out.exists():raise ValueError('Fresh preparation')
 out.mkdir(parents=True)
 c=read('tools/m4-lockit-source/continuity.py');c=replace(c,"'selected-table.bin',124","'selected-table.bin',125");c=replace(c,"'registration-roots.bin',96","'registration-roots.bin',97");save('continuity125.py',c)
 f=read('tools/m4-lockit-source/final_observer124_v2.py')
 f=replace(f,'  interface=ROOT/',"  self.tree_specs=[dict(root=0x4b7f70,CALL_pc=site,requested_size=24,publication=0,publication_PC=0,publication_owner=None)for site in(0x4ba306,0x4ba33c,0x4bab32)]\n  self.specs+=self.tree_specs;self.fs_specs+=self.tree_specs\n  interface=ROOT/")
 anchor="  if event=='returned'and data['caller']:"
 addition="""  if event=='write-after'and data['domain']=='source'and self.root==0x4b7f70 and data['bytes']==4 and data['pc']in(0x4ba315,0x4ba347,0x4bab9c,0x4babac):
   # The current pointer value and literal source publication identify an
   # allocation occurrence. Repeated CALL4BAB32 never uses first(root,site).
   proof=m.tree_publications[-1];need((proof['pc'],proof['address'],proof['value'])==(data['pc'],data['address'],data['value']),'Exact committed source tree primary publication')
   candidates=[r for r in self.mfc if r['words'][18]==proof['generation']and r['words'][16]==data['value']]
   need(len(candidates)==1,'One actual current tree owner generation per publication');w=candidates[0]['words'];need(w[23]==0 and w[4]==proof['owner_CALL_pc'],'Publication binds same literal allocation occurrence');w[23]+=1;COUNTS['exact_tree_primary_publications']+=1
"""
 f=replace(f,anchor,addition+anchor)
 for a,b in [('==58','==65'),('Exact58','Exact65'),('and58','and65'),('==78','==85'),('==96','==97'),('selected96','selected97'),('+=8','+=34'),('{96+n}','{97+n}'),('complete124','complete125'),('+=96','+=97'),('+=58','+=65'),('+=78','+=85'),('allocations=58','allocations=65')]:f=replace(f,a,b)
 f=f.replace('across47 MFC initializer roots','across48 MFC initializer roots')
 save('final_observer125.py',f)
 for file,name,provider in [('compare_connected_v7.py','compare_connected125.py',False),('compare_provider124_v8.py','compare_provider125.py',True)]:
  s=read('tools/m4-lockit-source/'+file)
  s=replace(s,"sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))","sys.path.insert(0,str(ROOT/'tools/m4-lockit-source'));sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))")
  s=replace(s,'import responses_v3 as R','import responses125 as R')
  s=replace(s,'import continuity as A','import continuity125 as A\nimport native_tree_relations_v4 as T')
  if provider:s=replace(s,'import final_observer124_v2 as F','import final_observer125 as F')
  else:
   s=replace(s,'B.R=R',"""class SourceResponses(R.ActualResponses):
 def __call__(self,m,target):
  mfc=any(f[0]in(0x5abd26,0x5f401ea0)for f in m.call_stack);duplicate=any(f[0]==0x78010a6d for f in m.call_stack);n=len(self.allocations);super().__call__(m,target)
  if len(self.allocations)>n:self.allocations[-1]['kind']=4 if mfc else 3 if duplicate else 1
R.ActualResponses=SourceResponses
B.R=R""")
  s=replace(s,"out=ROOT/'reports/m4-lockit-source'/name","out=ROOT/'reports/m4-tree-source'/name")
  s=replace(s,'continuity_rows=[]','continuity_rows=[];tree_rows=[]')
  s=replace(s,"ROOT/'tools/m4-lockit-source/game_model.py'","ROOT/'tools/m4-tree-source/game_model_v4.py'")
  s=replace(s,"prep=pin(ROOT/'reports/m4-lockit-native/preparation-r3/report.json','4c28406fb33cc34976b754ceedd0203540be80535c557a79b322407aae342b7d')","prep=pin(ROOT/'reports/m4-tree-native/preparation-r5/report.json','9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2')")
  s=replace(s,"op=pin(ROOT/'reports/m4-lockit-original/original-validation-r2/report.json','4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3')","op=pin(ROOT/'reports/m4-tree-original/original125-validation-r1/report.json','5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534')")
  s=replace(s,"roots={r['entry']:r['registration']['callback']for r in rootrows};","roots={r['entry']:r['registration']['callback']for r in rootrows};roots[0x4b7f70]=0x4b7fa0;")
  s=replace(s,"ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json'","ROOT/'reports/m4-tree-source/recovery-r1/instruction-contracts.json'")
  s=replace(s,"len(order)==124","len(order)==125")
  s=replace(s,'  FS_READ_BIAS=',"  for f in json.loads(pin(ROOT/'reports/m4-tree-source/recovery-r1/FS-frame-contracts.json').read_bytes()):\n   for k,kind in(('read',0),('install',1),('restore',2)):FS_SPECS[f[k]]=(kind,f['entry'],f['handler'])\n  FS_READ_BIAS=")
  s=replace(s,"pin(ROOT/'tools/m4-lockit-source/continuity.py')","pin(ROOT/'tools/m4-tree-source/continuity125.py')")
  s=replace(s,"need(len(image_raw)==320,'Exactly eight genuine native CS40 images')","need(len(image_raw)==34*40,'Exactly34 genuine native CS40 images')")
  s=replace(s,'len(expected_callbacks)==96','len(expected_callbacks)==97')
  s=replace(s,'All96 actual','All97 actual')
  s=replace(s,"counts['literal_Lockit_CALL_RET_pairs']+=8;counts['actual_native_CS40_source_API_relations']+=8","counts['literal_Lockit_CALL_RET_pairs']+=34;counts['actual_native_CS40_source_API_relations']+=34")
  s=replace(s,"len(fs_observations)==57","len(fs_observations)==78")
  s=replace(s,'All57 normal','All78 normal')
  s=replace(s,'len(fsframes)==19 and len(rawrecords)==38','len(fsframes)==26 and len(rawrecords)==52')
  s=replace(s,'Actual19 normal game frames and38','Actual26 normal game frames and52')
  s=replace(s,'index==19','index==26')
  # The old four-root derivation output remains ABI-compatible; all34 API
  # relations are retained, and the full new tree result is exported separately.
  anchor="     need(not stack and index==26,'All normal nested game frames close');"
  insert="""     result=machine.tree_result();tree_counts=T.verify(a,stem,result,responses.lockit_relations,C,checkpoint_index)
     for key,value in tree_counts.items():counts[key]+=value
     for owner in result['owners']:
      p=stem+'locale-allocation-'+str(owner['generation']);raw=bytes.fromhex(owner['source_final_hex']);allocation=next(v for v in responses.allocations if v['generation']==owner['generation'])
      equal(allocation['initial'],a.data(p+'-initial.bin'),'Whole tree genuine acquired owner vector');equal(machine.bytes(owner['guest'],allocation['mapped']),a.data(p+'-owned-page.bin'),'Whole tree mapped private page');equal(raw,a.data(p+'-owned-page.bin')[:owner['capacity']],'Whole native tree capacity bytes including untouched tail');counts['whole_native_tree_owner_backings']+=1
     tree_rows.append(dict(level=level,sequence=seq,source=result,API_relations=responses.lockit_relations,counts=tree_counts))
"""
  s=replace(s,anchor,insert+anchor)
  s=s.replace('persistent124','persistent125').replace('native124','native125').replace('selected124','selected125')
  if not provider:
   s=replace(s,"finally:a.close();a.entries.clear();a.bundles.clear();del a","finally:\n    a.close();a.entries.clear()\n    for closed_bundle in a.bundles:closed_bundle._entries.clear()\n    a.bundles.clear();del a")
   s=replace(s,"counts['persistent125_sequences']+=1","counts['persistent125_sequences']+=1;print(json.dumps(dict(source_case_passed=True,level=level,sequence=seq,API_count=responses.index)),flush=True)")
  else:
   s=replace(s,"F.COUNTS['complete124_provider_sequences']","F.COUNTS['complete125_provider_sequences']") if "F.COUNTS['complete124_provider_sequences']"in s else s
   s=replace(s,"need(F.COUNTS['complete125_provider_sequences']==12,'All12 complete persistent125 provider lifecycles')","need(F.COUNTS['complete125_provider_sequences']==12,'All12 complete persistent125 provider lifecycles')")
  s=replace(s,"('FS-source-derivations.json',FS_rows)","('Tree-source-derivations.json',tree_rows),('FS-source-derivations.json',FS_rows)")
  anchor='  passed=True'
  pins="  for file in ('game_model_v4.py','responses125.py','native_tree_relations_v4.py','continuity125.py','final_observer125.py','prepare_connected125.py'):pin(ROOT/'tools/m4-tree-source'/file)\n  for file in ('game_model_v3.py','game_model.py'):pin(ROOT/'tools/m4-tree-source'/file)\n"
  s=replace(s,anchor,pins+anchor)
  save(name,s)
 PINS[str(Path(__file__).resolve())]=sha(__file__)
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Prepared additive literal125 source/provider adapters; no execution credit',files=PINS),indent=2)+'\n')
 print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main()
