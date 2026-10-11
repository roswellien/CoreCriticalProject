"""Independent physical i386 encoding and actual finite helper observations."""
from pathlib import Path
import importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def encoded_capture(site,kind):
 code=bytearray();rel=[]
 def b(h):code.extend(bytes.fromhex(h))
 def absolute(symbol,addend=0,typ=6):rel.append((len(code),symbol,typ));code.extend(struct.pack('<I',addend))
 # Architectural registers saved using neutral absolute MOVs before changing ESP.
 for i,op in enumerate(('a3','890d','8915','891d','8925','892d','8935','893d')):b(op);absolute('_vtable_cpu',4*i)
 b('c705');absolute('_vtable_cpu',36);code.extend(struct.pack('<I',site));b('c705');absolute('_vtable_point');code.extend(struct.pack('<I',kind))
 host=len(code);b('8b25');absolute('_mixed_host_esp');first_stack=len(code);b('9c8f05');absolute('_vtable_cpu',32)
 b('64a100000000a3');absolute('_vtable_head');b('0fae05');absolute('_vtable_fx');b('d935');absolute('_vtable_env');b('d925');absolute('_vtable_env')
 b('e8');absolute('_vtable_observe',0,0x14);b('0fae0d');absolute('_vtable_fx');b('d925');absolute('_vtable_env');b('ff35');absolute('_vtable_cpu',32);b('9d')
 for i,op in enumerate(('a1','8b0d','8b15','8b1d','8b25','8b2d','8b35','8b3d')):
  if i!=4:b(op);absolute('_vtable_cpu',4*i)
 restore=len(code);b('8b25');absolute('_vtable_cpu',16)
 return code,rel,dict(host_stack=host,first_stack=first_stack,source_stack_restore=restore,source_replay=len(code))
def main(a,pin,out,counts,build,prep,link):
 spec=importlib.util.spec_from_file_location('retained_physical_i386_COFF_reader',pin(R/'tools/m4-fs-source/observer_attribution.py'));C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
 obj=pin(build/'build-x86/mw34_joint_startup120_original.dir/Release/vtable_observer_x86.obj');need('VTABLE_OBSERVER_X86.OBJ'in link.upper(),'Exact new observer object in actual final link')
 symbols,sections=C.parse_coff(obj.read_bytes());hooks=json.loads(pin(prep/'vtable-hook-bindings.json').read_bytes());ranges={};facts=[]
 for h in hooks:
  code,rel,marks=encoded_capture(h['PC'],h['kind']);code.extend(bytes.fromhex(h['replayed_bytes']))
  if h['kind']==0:code.extend(bytes.fromhex('ff25'));rel.append((len(code),'_vtable_continue_'+format(h['PC'],'x'),6));code.extend(bytes(4))
  target='_'+h['declared_observer'];d=[q for q in symbols.values()if q['name']==target];need(len(d)==1,'Unique true COFF indirect observer');d=d[0];need(d['storage']==2 and d['type']==0x20 and d['section']>0,'External i386 function symbol')
  s=sections[d['section']];need(s['characteristics']&0x20000000,'Executable actual COFF section');start=d['value'];raw=s['bytes'][start:start+len(code)];need(raw==code,'Every actual compiled preservation/source replay byte independently derived')
  observed=[(pos-start,n,t)for pos,n,t in s['relocations']if start<=pos<start+len(code)];need(observed==rel,'All independently derived relocation types/symbols/addends exact')
  need(marks['first_stack']==marks['host_stack']+6 and marks['source_replay']==marks['source_stack_restore']+6,'Authentic ESP saved before stack instruction, restored before source replay')
  ranges.setdefault(d['section'],[]).append((start,start+len(code)));facts.append(dict(PC=h['PC'],bytes=len(code),marks=marks,relocations=len(rel)))
 for index,rs in ranges.items():
  rs.sort();need(rs[0][0]==0 and rs[-1][1]==len(sections[index]['bytes'])and all(x[1]==y[0]for x,y in zip(rs,rs[1:])),'Complete executable indirect observer section covered')
 need(len(facts)==6,'All six true helper entry/preRET trampolines');counts['compiled_indirect_trampolines']=6;counts['indirect_compiled_bytes']=sum(q['bytes']for q in facts)
 inputs=json.loads(pin(R/'reports/m4-next-source/recovery-r1/indirect-call-inputs.json').read_bytes());contracts=inputs if isinstance(inputs,list)else inputs['calls'];groups={}
 for row in contracts:groups.setdefault(row['root'],[]).append(row)
 order=json.loads(pin(R/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())['selected_order']
 pairs=[]
 for seq in range(6):
  for phase,item in enumerate(order):
   stem=f'phase/{seq}/{phase}/';n=struct.unpack('<I',a.data(stem+'vtable-count.bin'))[0];data=a.data(stem+'vtable-snapshots.bin');expected=groups.get(item['entry'],[]);need(n==2*len(expected)and len(data)==n*660,'Only declared source-reached authentic entry/preRET pairs')
   for i,c in enumerate(expected):
    x=data[i*1320:i*1320+660];y=data[i*1320+660:(i+1)*1320];u=struct.unpack_from('<16I',x);v=struct.unpack_from('<16I',y);cpu=struct.unpack_from('<10I',x,64);after=struct.unpack_from('<10I',y,64);frame=struct.unpack_from('<4I',x,644)
    target=c['target'];ret_site={0x40e820:0x40e827,0x59ff00:0x59ff0d,0x59ff80:0x59ffa1}[target]
    need(u[:9]==(1,2*i,item['entry'],0,target,target,c['CALL_pc'],c['slot'],target),'Exact actual target/source CALL/table-cell identity')
    need(v[:9]==(1,2*i+1,item['entry'],1,ret_site,target,c['CALL_pc'],c['slot'],target),'Exact true preRET identity')
    need(u[9:]==v[9:]and cpu[1]==after[1]==c['entry_ECX']and cpu[4]==after[4]==u[12]and cpu[9]==target and after[9]==ret_site,'FS0/object/frame/API count preserved through integer-only target')
    need(frame[0]==c['return_pc']and x[644:]==y[644:]and(c.get('argument')is None or frame[1]==c['argument']),'Complete actual genuine CALL argument frame and RET cleanup contract')
    need(x[104:644]==y[104:644],'Complete actual helper hardware FX and legacy ENV unchanged')
    need(all(cpu[k]==after[k]for k in(1,3,4,5,6,7)),'Full other GPR conservation')
    if target==0x40e820:
     need(after[0]==0 and cpu[2]==after[2]and cpu[8]==after[8],'Exact zero setter EAX and neutral MOV flags/EDX')
    elif target==0x59ff00:
     need(after[0]==12 and after[2]==12,'Literal physical global0C OR zero source object field')
     need(after[8]&0x8c5==4 and(cpu[8]&~0x8d5)==(after[8]&~0x8d5),'All defined source OR flags; exact preserved nonarithmetic bits, AF explicitly undefined')
    else:
     need(frame[1]==0 and after[0]==0 and cpu[2]==after[2],'Genuine zero-argument path excludes any pointee read')
     need(after[8]&0x8c5==0x44 and(cpu[8]&~0x8d5)==(after[8]&~0x8d5),'All defined TEST-zero flags and exact preserved other bits')
    pairs.append(dict(sequence=seq,phase=phase,target=target,frame=u[12],return_PC=frame[0],physical_RET_cleanup=c['RET_cleanup'],postRET_PC_derived=frame[0],postRET_ESP_derived=u[12]+4+c['RET_cleanup'],actual_postRET_observed=False))
    counts['actual_indirect_entry_preRET_pairs']+=1;counts['actual_indirect_fullCPU_FX_ENV_relations']+=2;counts['actual_indirect_complete_frame_relations']+=1
 need(len(pairs)==36,'All six calls in each genuine original sequence');(out/'indirect-observer-facts.json').write_text(json.dumps(dict(compiled=facts,actual_pairs=pairs),indent=2)+'\n');pin(out/'indirect-observer-facts.json');pin(__file__)
