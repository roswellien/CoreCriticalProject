"""Read-only physical/source transparency audit of original116 observations."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=R/'reports/m4-container-review'/name;need(not out.exists(),'Fresh review');out.mkdir(parents=True);pins={};p=R/'reports/m4-container-source/original-preparation-r2'
 def pin(q,h=None):
  q=Path(q).resolve();v=sha(q);need(h is None or h==v,'Pinned physical input '+str(q));need(str(q)not in pins or pins[str(q)]==v,'Stable input');pins[str(q)]=v;return q
 prep=json.loads(pin(p/'report.json','fc3ce8ef54040236bced7072b3c121a0a7121c19ca81ef6e19ae0f54d5a06c49').read_bytes());need(prep['passed'],'Emitted bounded observer preparation')
 for q in ('reference.cpp','reference_x86.asm','fs_observer_x86.asm','nullfree_observer_x86.asm','fs-hook-bindings.json','nullfree-hook-bindings.json','spec.hpp'):pin(p/q,prep['files'][str(p/q)])
 s=importlib.util.spec_from_file_location('observer_physical_PE',pin(R/'tools/analysis/pe.py'));PE=importlib.util.module_from_spec(s);s.loader.exec_module(PE)
 images={}
 for key,q,h in(('game','MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('crt','local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')):images[key]=PE.PEImage(pin(R/q,h).read_bytes())
 def physical(pc,raw):
  pe=images['crt'if pc>=0x78000000 else'game'];b=bytes.fromhex(raw);need(pe.read(pe.rva_range(pc-pe.image_base,len(b))[0],len(b))==b,'Exact original hook span '+hex(pc))
 cpp=(p/'reference.cpp').read_text();fs=(p/'fs_observer_x86.asm').read_text();nf=(p/'nullfree_observer_x86.asm').read_text();ref=(p/'reference_x86.asm').read_text();regs=('eax','ecx','edx','ebx','esp','ebp','esi','edi')
 def capture(part,label,observer):
  save=[f'mov DWORD PTR {label}_cpu[{i*4}],{reg}'for i,reg in enumerate(regs)]
  restore=[f'mov {reg},DWORD PTR {label}_cpu[{i*4}]'for i,reg in enumerate(regs)if reg!='esp']+[f'mov esp,DWORD PTR {label}_cpu[16]']
  lines=[q.strip()for q in part.splitlines()if q.strip()]
  for q in save+restore:need(lines.count(q)==1,'Exactly one saved/restored architectural register '+q)
  switch=lines.index('mov esp,mixed_host_esp');need(all(lines.index(q)<switch for q in save),'Save source ESP/GPR before any observer host-stack push')
  sequence=['pushfd',f'pop DWORD PTR {label}_cpu[32]',f'fxsave {label}_fx',f'fnstenv {label}_env',f'fldenv {label}_env',f'call {observer}',f'fxrstor {label}_fx',f'fldenv {label}_env',f'push DWORD PTR {label}_cpu[32]','popfd']
  positions=[];start=switch
  for q in sequence:
   pos=lines.index(q,start);positions.append(pos);start=pos+1
  need(all(lines.index(q)>positions[-1]for q in restore),'Restore flags/FX/full ENV before saved GPR/source ESP')
  need(all(q.startswith(('mov ','pushfd','pop ','fxsave ','fnstenv ','fldenv ','call ','fxrstor ','push ','popfd'))for q in lines),'Bounded observation capture has no hidden flag-changing instruction or source-stack push')
 hooks=json.loads((p/'fs-hook-bindings.json').read_bytes());need(len(hooks)==30,'Thirty physical FS spans')
 for row in hooks:
  pc=row['PC'];raw=row['raw_bytes'];physical(pc,raw);need(row['continuation']==pc+len(bytes.fromhex(raw)),'Literal FS continuation')
  name=row['declared_observer'];part=fs.split(name+' PROC\n',1)[1].split(name+' ENDP',1)[0];before,after=part.split(' db ',1);rawline,after=after.split('\n',1);got=bytes(int(q.strip()[:-1],16)for q in rawline.split(','));need(got==bytes.fromhex(raw),'FS trampoline replays exact physical instruction')
  before=before.split('\n',1)[1];after,jump=after.rsplit(' jmp ',1);need(jump.strip()==f'DWORD PTR fs_continue_{pc:x}','Exact original PC continuation rather than a synthesized RET')
  capture(before,'fs_before','fs_observe_before');capture(after,'fs_after','fs_observe_after')
 nullhooks=json.loads((p/'nullfree-hook-bindings.json').read_bytes());need(len(nullhooks)==2,'Two exact null-free original spans')
 for row in nullhooks:physical(row['pc'],row['raw'])
 entry=nf.split('nullfree_entry_hook PROC\n',1)[1].split('nullfree_entry_hook ENDP',1)[0];before,tail=entry.split(' db ',1);capture(before,'nullfree','nullfree_observe');need(tail.strip()=='055h,08bh,0ech,06ah,0ffh\n jmp DWORD PTR nullfree_entry_continue','Replay original PUSH EBP/MOV EBP,ESP/PUSH -1 after true entry observation')
 ret=nf.split('nullfree_ret_hook PROC\n',1)[1].split('nullfree_ret_hook ENDP',1)[0];need(ret.startswith(' db 05fh,05eh,05bh,0c9h\n'),'Original POP EDI/ESI/EBX/LEAVE before RET-point observation');capture(ret.split('\n',1)[1].rsplit(' db ',1)[0],'nullfree','nullfree_observe');need(ret.rstrip().endswith('db 0c3h'),'Genuine final RET, no synthesized return')
 need('extern const unsigned nullfree_entry_continue=0x78001395' in cpp,'Original prolog continuation address')
 enter=ref.split('mixed_enter PROC\n',1)[1].split('mixed_enter ENDP',1)[0];need(enter.index('mov mixed_host_esp,esp')<enter.index('mov esp,DWORD PTR mixed_input[16]'),'Observer host stack saved before switching to source stack')
 observe=cpp.split('void nullfree_observe(){',1)[1].split('\n}\nvoid nullfree_entry_hook',1)[0]
 need('w[0]==0x5f40178c&&w[1]==0&&w[2]==b.CALL_pc+5&&w[3]==0'in observe,'Original CRT/MFC/game return frames and genuine zero arguments authenticated')
 need('before.frame!=e.frame||before.head!=e.head||before.API_count!=e.API_count||std::memcmp(before.words,e.words,16)'in observe,'True frame/FS0/API count/full argument frame conservation')
 need('remove_CRT_hooks();registry_cleanup.restore()'in cpp and 'install_CRT_hooks();'in cpp,'CRT observations removed before genuine host-stack positive cleanup and reinstalled for next sequence')
 pin(__file__);report=dict(passed=True,scope='Read-only physical/emitted-source observer transparency review; no original execution, compiled-hook or initializer credit.',physical_FS_spans=30,physical_nullfree_spans=2,saved_and_restored_GPR_flags_FX_ENV_boundaries=62,source_ESP_saved_before_host_push=True,exact_prolog_epilog_RET_replay=True,original_import_and_zero_argument_frames_checked=True,positive_cleanup_observer_removal_checked=True,compiled_hook_check_pending=True,files=pins,physical_closure=verify_manifest(pins));(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
