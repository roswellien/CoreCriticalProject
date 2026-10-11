"""Add actual HeapReAlloc API-produced backing capture before guest writes."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[2];parent=R/'reports/m4-startup138-original/preparation-r7';out=parent.with_name('preparation-r8');assert not out.exists();out.mkdir()
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
report=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2'
for p in parent.iterdir():
 if p.is_file()and p.name not in('report.json','pins.json'):shutil.copyfile(p,out/p.name)
base=(parent/'reference.cpp').read_text();text=base;changes=[]
def one(old,new):
 global text
 assert text.count(old)==1,old[:100];pos=text.index(old);changes.append(dict(position=pos,old=old,new=new));text=text[:pos]+new+text[pos+len(old):]
one('if(i>=256||registry_API_kind!=0||!registry_API_after.eax)return;', 'if(i>=256||(registry_API_kind!=0&&registry_API_kind!=3)||!registry_API_after.eax)return;')
one('std::memcpy(registry_initial_bytes[i],pointer,size);fs_observe_allocation', 'std::memcpy(registry_initial_bytes[i],pointer,size);if(registry_API_kind!=0)return;fs_observe_allocation')
one('for(unsigned ai=0;ai<registry_API_count;++ai)if(registry_API_ledger[ai].kind==0&&registry_API_ledger[ai].after.eax){require(registry_initial_sizes[ai]>=registry_API_ledger[ai].args[2]&&registry_initial_sizes[ai]<=1024,"Actual HeapAlloc initial backing captured before guest writes");', 'for(unsigned ai=0;ai<registry_API_count;++ai)if((registry_API_ledger[ai].kind==0||registry_API_ledger[ai].kind==3)&&registry_API_ledger[ai].after.eax){const auto requested=registry_API_ledger[ai].args[registry_API_ledger[ai].kind==3?3:2];require(registry_initial_sizes[ai]>=requested&&registry_initial_sizes[ai]<=1024,"Actual HeapAlloc/HeapReAlloc API-return backing captured before guest writes");')
reverse=text
for d in reversed(changes):
 p=d['position'];assert reverse[p:p+len(d['new'])]==d['new'];reverse=reverse[:p]+d['old']+reverse[p+len(d['new']):]
assert reverse==base;(out/'reference.cpp').write_text(text)
assert 'if(registry_API_kind!=0)return;fs_observe_allocation'in text
assert text.count('kind==0&&registry_API_ledger[ai].after.eax){const auto pointer')==1
files=dict(report['files']);files[str(Path(__file__).resolve())]=sha(Path(__file__))
for p in out.iterdir():
 if p.is_file():files[str(p.resolve())]=sha(p)
report.update(scope='Unbuilt original138 derivative: full actual HeapReAlloc API-return backing observed before guest writes; unchanged kind0 allocation ownership observers and kind0 final exports',parent_preparation_path=str(parent/'report.json'),parent_preparation_sha256=sha(parent/'report.json'),contracts=str(out/'contracts.json'),realloc_observer_delta=changes,exact_inverse_restores_parent_reference=True,HeapReAlloc_initial_backing_observed_before_guest_writes=True,kind0_ownership_callbacks_unchanged=True,complete_widget_gate=False,files=files)
q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files={**files,str(q.resolve()):sha(q)}),indent=2)+'\n');print(q,sha(q))
