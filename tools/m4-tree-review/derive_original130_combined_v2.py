from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-tree-review/review_original130_combined.py';raw=p.read_text()
a='"actual compiled observer FS head matches literal entry/return head"in source.lower()';b='"actual compiled observer fs head matches literal entry/return head"in source.lower()'
assert raw.count(a)==1
raw=raw.replace(a,b)
a="need('mov format_head,eax'in body and 'fxrstor format_fx'in body and 'fldenv format_env'in body,'Actual whole architectural capture/restoration source');functions.append(function)"
b="need('mov format_head,eax'in body and 'fxrstor format_fx'in body and 'fldenv format_env'in body,'Actual whole architectural capture/restoration source');need(body[body.index('mov esp,mixed_host_esp'):body.index('mov eax,dword ptr fs:[0]')].split()==['mov','esp,mixed_host_esp','pushfd','pop','dword','ptr','format_cpu[32]','cld'],'Exactly ESP switch/PUSHFD/flag-save/CLD before FS head read, no FS write');functions.append(function)"
assert raw.count(a)==1
raw=raw.replace(a,b)
target=p.with_name('review_original130_combined_v2.py');assert not target.exists();target.write_text(raw)
print(json.dumps(dict(parent_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),derived_sha256=hashlib.sha256(target.read_bytes()).hexdigest())))
