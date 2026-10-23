"""Prepared ROOT-only pure finite heap field controls, no readers/models."""
import importlib.util,struct,copy
from pathlib import Path
def main():
 p=Path(__file__).with_name('native_heap_field_cut_v1.py');s=importlib.util.spec_from_file_location('HF',p);H=importlib.util.module_from_spec(s);s.loader.exec_module(H)
 heap=[[1,0x20001000+4*i,0,4,0]for i in range(36)];heap[8]=[0x780039d8,0x78035000,H.TOKEN,4,1];heap[31]=[0x780039eb,0x78035004,1,4,1]
 provider=[[0x78001306,0x78035004,1,4,0],[0x78001379,0x78035000,H.TOKEN,4,0]];raw=copy.deepcopy(heap)+[[2,0x20001000,0,4,0]]+copy.deepcopy(provider)
 row=dict(source_seed=False,AFTER_seed=False,whole_native_component_journals_compared=True,whole_native_State_CPU_FX_compared=True,full_literal_journal_preserved_during_instruction_guards=True,provider_source_accesses=provider,whole_literal_source_accesses=provider)
 w=[1,0,1,0,4096,0,0x100000001,H.TOKEN,0,0,0,0x100000001,0x20001848,0x780039d6,0x20001858,0x780039d6]
 def run(r,h,q,c):return H.prove(r,struct.pack('<640I',*(sum(h,[])+[0]*460)),b''.join(struct.pack('<IIQII',*v)for v in q),struct.pack('<16Q',*c))
 assert run(row,heap,raw,w)['memory_hex']==struct.pack('<2I',H.TOKEN,1).hex();names=[]
 def reject(name,change):
  r,h,q,c=copy.deepcopy((row,heap,raw,w));change(r,h,q,c)
  try:run(r,h,q,c)
  except (ValueError,AssertionError,struct.error):names.append(name);return
  raise AssertionError('Accepted adverse '+name)
 reject('source-seed',lambda r,h,q,c:r.update(source_seed=True));reject('AFTER-seed',lambda r,h,q,c:r.update(AFTER_seed=True));reject('unproven-whole-provider',lambda r,h,q,c:r.update(full_literal_journal_preserved_during_instruction_guards=False))
 for at,name in [(0,'publication-PC'),(1,'publication-address'),(2,'publication-token'),(3,'publication-width'),(4,'publication-write')]:
  reject(name,lambda r,h,q,c,at=at:(h[8].__setitem__(at,h[8][at]^1),q[8].__setitem__(at,q[8][at]^1)))
 reject('wrong-owned-token',lambda r,h,q,c:c.__setitem__(7,H.TOKEN^1));reject('wrong-native-owner',lambda r,h,q,c:c.__setitem__(11,c[6]+1));reject('unowned-API-result',lambda r,h,q,c:c.__setitem__(6,0));reject('wrong-API-frame',lambda r,h,q,c:c.__setitem__(12,c[12]+4))
 reject('raw-provider-mismatch',lambda r,h,q,c:q[-1].__setitem__(2,H.TOKEN^1));reject('duplicate-provider-scope',lambda r,h,q,c:q.extend(copy.deepcopy(r['provider_source_accesses'])))
 reject('intervening-token-write',lambda r,h,q,c:q.insert(36,[9,0x78035000,H.TOKEN,4,1]));reject('unaligned-intervening-overlap',lambda r,h,q,c:q.insert(36,[9,0x78034fff,0,2,1]));reject('intervening-mode-write',lambda r,h,q,c:q.insert(36,[9,0x78035007,0,1,1]))
 reject('own-first-read-PC',lambda r,h,q,c:r['whole_literal_source_accesses'][0].__setitem__(0,0));reject('own-first-read-width',lambda r,h,q,c:r['whole_literal_source_accesses'][0].__setitem__(3,1));reject('own-first-read-value',lambda r,h,q,c:r['whole_literal_source_accesses'][0].__setitem__(2,2));reject('own-before-write',lambda r,h,q,c:r['whole_literal_source_accesses'].insert(0,[9,0x78035003,0,2,1]));reject('own-late-write',lambda r,h,q,c:r['whole_literal_source_accesses'].append([9,0x78035000,H.TOKEN,4,1]))
 print(dict(passed=True,adverse_controls=len(names),names=names,reader_opened=False,CPU_model_executed=False,whole_page_claim=False))
if __name__=='__main__':main()
