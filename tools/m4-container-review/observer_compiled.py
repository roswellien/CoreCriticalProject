"""Independent original observer COFF/link and actual null-frame audit."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,subprocess,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=R/'reports/m4-container-review'/name;need(not out.exists(),'Fresh independent compiled observer audit');out.mkdir(parents=True);pins={};counts=collections.Counter()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact pinned file '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable physical file');pins[str(p)]=v;return p
 proof=json.loads(pin(R/'reports/m4-container-review/observer-static-r1/report.json','f6f8b3d9f5d278af06b52bac560daaac76105ba43b0847d6be128813591bbba4').read_bytes());need(proof['passed'],'Independent physical/emitted-source transparency gate')
 for p,h in proof['files'].items():pin(p,h)
 b=R/'reports/m4-container-source/original-build-r2';build=json.loads(pin(b/'build.json','8b1e7694bf3d9a651b729dc6740310c72c1b7409918de62c9411394da3021541').read_bytes());need(build['passed'],'Actual fresh original compilation')
 val=json.loads(pin(R/'reports/m4-container-source/original-validation-r1/report.json','4012b8c62c821131469e012f1e10ba31b621c524c6b0a9b042d5150dd2f3067b').read_bytes());need(val['passed'],'Actual original116 structural validation')
 for p,h in json.loads(pin(b/'pins.json').read_bytes())['files'].items():pin(p,h)
 release=b/'build-x86/mw34_joint_startup116_original.dir/Release';llvm=pin(R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe')
 tlogs=list(release.rglob('link.command.1.tlog'));need(len(tlogs)==1,'One actual original final link command');link=pin(tlogs[0]).read_text(encoding='utf-16');objects={}
 for filename in('fs_observer_x86.obj','nullfree_observer_x86.obj'):
  obj=pin(release/filename);need(filename.upper()in link.upper(),'Actual observer COFF named in final link '+filename)
  raw=subprocess.run([str(llvm),'-dr',str(obj)],capture_output=True,check=True,creationflags=0x08000000).stdout.decode();dest=out/(filename+'.txt');dest.write_text(raw);pin(dest);objects[filename]=raw
 fs=objects['fs_observer_x86.obj'];nf=objects['nullfree_observer_x86.obj']
 for text,n in((fs,60),(nf,2)):
  for opcode in('pushfl','popfl','fxsave','fxrstor','fnstenv'):
   need(len(re.findall(r'\t'+opcode+r'\b',text))==n,'Every actual compiled preservation opcode '+opcode)
  need(len(re.findall(r'\tfldenv\b',text))==n*2,'Every compiled complete legacy ENV restore before/after C++ observer')
  need(len(re.findall(r'IMAGE_REL_I386_DIR32\s+_mixed_host_esp\b',text))==n,'Actual compiled host stack switch count')
 for row in json.loads(pin(R/'reports/m4-container-source/original-preparation-r2/fs-hook-bindings.json').read_bytes()):
  name='_'+row['declared_observer'];block=fs.split('<'+name+'>:',1)[1].split('\n\n',1)[0];need('IMAGE_REL_I386_DIR32\t_fs_continue_'+format(row['PC'],'x')in block,'Exact compiled source continuation relocation');counts['compiled_FS_trampolines']+=1
 need('55                           \tpushl\t%ebp'in nf and '6a ff' in nf and 'IMAGE_REL_I386_DIR32\t_nullfree_entry_continue'in nf,'Actual compiled original prolog and continuation')
 ret=nf.split('<_nullfree_ret_hook>:',1)[1];need(re.search(r'5f\s+popl\s+%edi',ret)and re.search(r'5e\s+popl\s+%esi',ret)and re.search(r'5b\s+popl\s+%ebx',ret)and re.search(r'c9\s+leave',ret)and re.search(r'c3\s+retl',ret),'Actual original literal POP/LEAVE/C3 return in compiled hook')
 spec=importlib.util.spec_from_file_location('original_observer_archive',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D);a=D.DirectSet(val['original_capture'],pin)
 bindings=json.loads(pin(R/'reports/m4-container-source/allocation-interface-r1/nullfree-inputs.json').read_bytes());rootbinding={q['root']:q for q in bindings};order=json.loads(pin(R/'reports/m4-container-source/recovery-r3/instruction-contracts.json').read_bytes())['selected_order']
 try:
  for seq in range(6):
   for phase,item in enumerate(order):
    stem=f'phase/{seq}/{phase}/';count=struct.unpack('<I',a.data(stem+'nullfree-count.bin'))[0];raw=a.data(stem+'nullfree-snapshots.bin');need(len(raw)==count*628,'Complete captured actual null snapshots')
    expected=2 if item['entry']in rootbinding else 0;need(count==expected,'Exactly genuine selected free(NULL) entry/RET pair')
    if not count:continue
    before,after=raw[:628],raw[628:];q=struct.unpack_from('<8I',before);z=struct.unpack_from('<8I',after);cpu=struct.unpack_from('<10I',before,32);retcpu=struct.unpack_from('<10I',after,32);words=struct.unpack_from('<4I',before,612);spec=rootbinding[item['entry']]
    need(q[:5]==(1,0,item['entry'],0,0x78001390)and z[:5]==(1,1,item['entry'],1,0x78001424),'Authentic literal original entry/preRET association')
    need(q[5:]==z[5:]and cpu[4]==retcpu[4]==q[5]and cpu[9]==q[4]and retcpu[9]==z[4],'Exact original frame/outerFS0/API conservation')
    need(words==(0x5f40178c,0,spec['CALL_pc']+5,0)and before[612:]==after[612:],'Complete original CRT/MFC/game import frames and zero arguments')
    need(before[72:612]==after[72:612],'Actual complete original FX/legacy ENV exact through literal nullfree')
    need(all(cpu[i]==retcpu[i]for i in(2,3,4,5,6,7))and retcpu[0]==retcpu[1]==q[6],'Literal nullfree nonvolatile/EDX/ESP preserved and actual EAX/ECX both saved game chain')
    need((retcpu[8]&0x8c5)==0x44 and(cpu[8]&~0x8d5)==(retcpu[8]&~0x8d5),'Actual TEST-zero flags with only source-defined arithmetic effects; AF excluded as undefined')
    events=a.data(stem+'fs-events.bin');need(len(events)%1216==0,'Complete original FS observation records');crt=[]
    for off in range(0,len(events),1216):
     e=events[off:off+1216];head=struct.unpack_from('<8I',e)
     if head[2]>=0x78000000:crt.append(e)
    need(len(crt)==3,'Three genuine nested CRTfree FS instructions')
    heads=[struct.unpack_from('<8I',e)for e in crt];need([h[2]for h in heads]==[0x7800139f,0x780013a6,0x78001419],'Exact literal nested free(NULL) chain read/install/restore')
    need(heads[0][4]==heads[0][5]==q[6]and heads[1][4]==q[6]and heads[1][5]==heads[1][6]and heads[2][4]==heads[1][5]and heads[2][5]==q[6],'Original inner CRT chain nested inside same actual game frame, fully restored')
    need(crt[1][112:124]==crt[1][124:136]==crt[2][112:124]==crt[2][124:136],'Exact full12B original inner frame conserved across installation/restoration')
    frame=struct.unpack_from('<3I',crt[1],112);need(frame==(q[6],0x7800ef03,0xffffffff),'Original inner frame saves exact outer game predecessor and literal handler/scope')
    counts['actual_nullfree_pairs']+=1;counts['actual_full_FX_ENV_pair_relations']+=1;counts['actual_import_frame_relations']+=1;counts['actual_nested_CRT_FS_records']+=3;counts['actual_full12B_nested_chain_relations']+=1
 finally:a.close()
 need(counts['actual_nullfree_pairs']==30,'All genuine six-sequence five nullfree boundaries reviewed')
 pin(__file__);report=dict(passed=True,scope='Independent actual original observer compiled COFF/final-link and thirty true free(NULL) frame/hardware/nested-chain audit. Whole initializer/source model remains separate; no unwind/handler paths claimed.',counts=dict(counts),compiled_hook_check_pending=False,full_GPR_flags_FX_ENV_preservation_code_checked=True,literal_void_EAX_not_synthesized=True,files=pins,physical_closure=verify_manifest(pins));(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
