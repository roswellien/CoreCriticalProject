"""Additive observation-only derivative; accepted116 source files unchanged."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main(name):
 out=ROOT/'reports/m4-vtable-review'/name;assert not out.exists();out.mkdir(parents=True);pins={};generated={}
 def pin(p):p=Path(p);pins[str(p.resolve())]=sha(p);return p
 def write(n,s):
  p=HERE/n
  if p.exists():assert p.read_text()==s,'Exact prior generated draft bytes '+str(p)
  else:p.write_text(s)
  generated[str(p.resolve())]=sha(p)
 prior=ROOT/'tools/m4-container-review'
 for n in('exact_equal.py','event_model.py','string_observer116.py'):write(n,pin(prior/n).read_text())
 s=pin(prior/'final_observer116_v2.py').read_text()
 s=s.replace("ROOT/'tools/m4-container-review/string_observer116.py'","ROOT/'tools/m4-vtable-review/string_observer116.py'")
 s=one(s,'from event_model import ContainerEvents','from event_model import ContainerEvents\nfrom vtable_model import VtableEvents')
 s=one(s,'self.container_tail_projections=0;self.container=ContainerEvents(self,borrowed,zero_frees,stores)','self.container_tail_projections=0;self.container=ContainerEvents(self,borrowed,zero_frees,stores);self.vtable=VtableEvents(self)')
 s=one(s,'super().string_event(m,event,data);self.mfc_event(m,event,data)','self.vtable.event(m,event,data);super().string_event(m,event,data);self.mfc_event(m,event,data)')
 s=one(s,'for key,value in self.container.dump(m,stage).items():COUNTS[key]+=value','for key,value in self.container.dump(m,stage).items():COUNTS[key]+=value\n  for key,value in self.vtable.dump(m,stage).items():COUNTS[key]+=value')
 s=s.replace('registry-replay-{88+n}','registry-replay-{92+n}').replace("complete116_provider_sequences","complete120_provider_sequences").replace("selected_registration_closures']+=88","selected_registration_closures']+=92")
 s=one(s,'initial_used=vector[\'next\']-vector[\'begin\'];capacity_steps=None;first_query_capacity=None;n=0','initial_used=vector[\'next\']-vector[\'begin\'];capacity_steps=(vector[\'capacity\']-initial_used)//4+1 if vector[\'capacity\'] else None;first_query_capacity=None;n=0;old_owner=(vector[\'native\'],vector[\'begin\'])\n  need(not vector[\'capacity\'] or vector[\'capacity\']>=initial_used,\'Carried source cached capacity covers actual selected used bytes\')')
 s=one(s,'if first_query_capacity is None:\n    queries=[f for f in responses.facts[first_API:responses.index]if f[\'name\']==\'HeapSize\'];need(len(queries)in(1,2),\'One genuine onexit msize plus optional genuine realloc-side msize on first replay\')','queries=[f for f in responses.facts[first_API:responses.index]if f[\'name\']==\'HeapSize\']\n   if first_query_capacity is None and queries:\n    need(len(queries)in(1,2),\'One genuine onexit msize plus optional genuine realloc-side msize on first reached query\')')
 s=one(s,"f['words'][16]==vector['native']and f['words'][22]==vector['begin']","(f['words'][16],f['words'][22])==old_owner")
 s=one(s,"capacity_steps=(first_query_capacity-initial_used)//4+1;COUNTS", "derived=(first_query_capacity-initial_used)//4+1;need(capacity_steps is None or capacity_steps==derived,'Carried cached capacity agrees with actual ordinary source msize before growth');capacity_steps=derived;COUNTS")
 write('final_observer120.py',s)
 s=pin(prior/'observe116_v2.py').read_text()
 s=s.replace('final_observer116_v2','final_observer120').replace('reports/m4-container-review','reports/m4-vtable-review').replace("ROOT/'tools/m4-container-source/game_model.py'","ROOT/'tools/m4-next-source/game_model.py'").replace('native116','native120').replace('full116','full120').replace('persistent116','persistent120').replace('independent116','independent120').replace('complete116','complete120')
 s=one(s,'0x736000,0x5f4cc000)','0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000)')
 s=one(s,"ROOT/'reports/m4-container-review'/name","ROOT/'reports/m4-vtable-review'/name") if "ROOT/'reports/m4-container-review'/name"in s else s
 s=one(s,"ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes());roots", "ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/fixed-roots.json').read_bytes());roots")
 s=s.replace("ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json'","ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json'").replace('len(order)==116','len(order)==120').replace('len(expected_callbacks)==88','len(expected_callbacks)==92').replace('All88','All92').replace('entire37pages','entire40pages')
 s=s.replace('o[153828:305380]','o[166116:329956]').replace('o[2276:153828]','o[2276:166116]')
 s=one(s,"pin(Path(__file__).with_name('event_model.py'));pin(Path(__file__).with_name('string_observer116.py'))", "pin(Path(__file__).with_name('event_model.py'));pin(Path(__file__).with_name('vtable_model.py'));pin(Path(__file__).with_name('string_observer116.py'))")
 write('observe120.py',s)
 pin(HERE/'vtable_model.py');pin(__file__)
 report=dict(passed=True,scope='Additive independent120 persistent provider/owner observation derivation only; no execution/admission',source_parents=pins,generated=generated,exact_equal_unchanged=sha(HERE/'exact_equal.py')==sha(prior/'exact_equal.py'),new_imported_providers=0,new_allocations=0,native_executed=False,original_executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
