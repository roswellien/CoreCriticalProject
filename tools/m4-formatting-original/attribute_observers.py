"""Exact compiled/link attribution for both genuine formatting original workers."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-formatting-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh exact formatting observer attribution');out.mkdir(parents=True);pins={};counts=collections.Counter();rows=[];passed=False;reader=None
 def pin(p,h=None):
  p=Path(p).resolve();v=pins.get(str(p))or sha(p);need(h is None or h==v,'Physical observer identity '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
 def module(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  P=module(ROOT/'tools/analysis/pe.py','format_attrib_PE');C=module(ROOT/'tools/m4-fs-source/observer_attribution.py','format_attrib_COFF');L=module(ROOT/'tools/m4-lockit-review/full_original_review.py','format_attrib_reused_pattern');D=module(ROOT/'tools/m4-crt-allocation-root/run_v2.py','format_attrib_direct')
  game=P.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  def physical(pe,a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
  funcs=[('strrchr',0,0x780264a9,0x4dea1b,bytes.fromhex('83c4083bc3'),0x5bb5a8),('malloc',1,0x780012b3,0x4deab7,bytes.fromhex('83c4043bc3'),0x5bb664),('sprintf',2,0x78022b9a,0x4dead7,bytes.fromhex('83c4108b442420'),0x5bb658)]
  def expected(pc,kind,replay,index,after):
   b,rel=L.expected_lockit(pc,kind,replay,'_format_continues'if after else None,None if after else'_format_targets');b=bytearray(b);rel=[(o,n.replace('_lockit_','_format_'),t)for o,n,t in rel];flags=[o for o,n,t in rel if n=='_format_cpu'and struct.unpack_from('<I',b,o)[0]==32];need(len(flags)==2,'Reviewed full flag save/restore pair');pos=flags[0]+4;b[pos:pos]=b'\xfc';rel=[(o+(o>=pos),n,t)for o,n,t in rel]
   tail=rel[-1];need(tail[1]==('_format_continues'if after else'_format_targets'),'Only typed full source continuation/provider tail slot');struct.pack_into('<I',b,tail[0],index*4);return bytes(b),rel
  template={};gate_paths=[('prefix-validation-r1','54199a2f52a1c7489ccc53a8722bf6dc1d06395e7c05c6043e84f82af5f1b3e4'),('trace-prefix-validation-r1','d410d2020a019e17e0ec88154520b8e89c165a5e52685c3b75c45fc274ddac25')]
  for gate_name,gate_sha in gate_paths:
   gate=read(BASE/gate_name/'report.json',gate_sha);execution=read(gate['execution_path'],gate['execution_sha256']);build=read(execution['build_path'],execution['build_sha256']);prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(all(x['passed']for x in(gate,execution,build,prep)),'Actual original positive gates')
   for p,h in prep['files'].items():pin(p,h)
   for p,h in read(Path(execution['build_path']).parent/'pins.json')['files'].items():pin(p,h)
   release=Path(execution['build_path']).parent/'build-x86/mw34_joint_startup124_original.dir/Release';symbols,sections=C.parse_coff(pin(release/'format_observer_x86.obj').read_bytes());defs={s['name']:s for s in symbols.values()if s['section']>0 and s['storage']==2};need(len([n for n in defs if n.startswith('_format_')])==6,'All six compiled formatting wrappers');links=list(release.rglob('link.command.1.tlog'));need(len(links)==1 and 'FORMAT_OBSERVER_X86.OBJ'in pin(links[0]).read_text(encoding='utf-16').upper(),'Actual observer included in final link')
   workerbytes=pin(build['worker'],build['worker_sha256']).read_bytes();worker=P.PEImage(workerbytes);need(worker.machine==0x14c and worker.image_base==0x18000000,'Genuine actual fixed-base i386 observer worker');shared={}
   reader=D.DirectSet(execution['original_capture'],pin);data=reader.data('phase/0/0.bin');pages=prep['observed_pages'];iat_offset=2276+pages.index(0x5bb000)*4096
   def executable(a):return any(s['executable']and worker.image_base+s['virtual_address']<=a<worker.image_base+s['virtual_address']+s['raw_size']for s in worker.sections)
   for name,index,entry,ret,replay,iat in funcs:
    need(physical(game,ret,len(replay))==replay,'Exact physical caller-return replay span')
    key=struct.pack('<2I',ret,len(replay));matches=[];start=0
    while True:
     p=workerbytes.find(key,start)
     if p<0:break
     if workerbytes[p+12:p+12+len(replay)]==replay:matches.append(p)
     start=p+1
    need(len(matches)==1,'Unique final compiled FormatHook source/target initializer');return_target=struct.unpack_from('<I',workerbytes,matches[0]+8)[0];entry_target=struct.unpack_from('<I',data,iat_offset+(iat&4095))[0]
    for after,target in[(0,entry_target),(1,return_target)]:
     symbol='_format_'+('return_'if after else'entry_')+name;b,rel=expected(ret if after else entry,index*2+after,replay if after else b'',index,after);definition=defs[symbol];sec=sections[definition['section']];actual=sec['bytes'][definition['value']:definition['value']+len(b)];actual_rel=[(o-definition['value'],n,t)for o,n,t in sec['relocations']if definition['value']<=o<definition['value']+len(b)];need(actual==b and actual_rel==rel,'Entire actual compiled wrapper bytes and exact typed relocations')
     if symbol in template:need(template[symbol]==(b,rel),'Normal and debugger worker wrapper code/relocations identical')
     else:template[symbol]=(b,rel)
     need(executable(target),'Actual linked source target belongs to current worker executable code');linked=physical(worker,target,len(b));normalized=bytearray(linked)
     for offset,sym,typ in rel:
      addend=struct.unpack_from('<I',b,offset)[0];value=struct.unpack_from('<I',linked,offset)[0];address=(value-addend)&0xffffffff if typ==6 else(target+offset+4+value-addend)&0xffffffff;need(typ in(6,0x14),'Only typed i386 DIR32/REL32 fields');need(sym not in shared or shared[sym]==address,'Stable actual shared compiled symbol '+sym);shared[sym]=address;normalized[offset:offset+4]=b[offset:offset+4]
     need(bytes(normalized)==b,'Every actual linked executable wrapper byte modulo exact relocation fields');counts['compiled_linked_functions']+=1;counts['compiled_linked_bytes']+=len(b);counts['compiled_linked_relocations']+=len(rel);rows.append(dict(gate=gate_name,symbol=symbol,kind=index*2+after,source_PC=ret if after else entry,actual_worker_target=target,target_source='Actual source owning IAT in whole game BEFORE page'if not after else'Unique physical final FormatHook initializer consumed by checked source patch installer',bytes=len(b),relocations=len(rel),replay_hex=replay.hex()if after else'',tail_field_index=index,source_return_before_caller_cleanup=bool(after)))
   need(physical(worker,shared['_format_continues'],12)==struct.pack('<3I',0x4dea20,0x4deabc,0x4deade),'All actual physical caller continuation DWORDs');need(tuple(struct.unpack('<3I',reader.data('formatting/import-targets.bin')))==(0x780264a9,0x780012b3,0x78022b9a),'Actual initialized named source provider targets');need(any(s['writable']and worker.image_base+s['virtual_address']<=shared['_format_targets']<worker.image_base+s['virtual_address']+s['virtual_size']for s in worker.sections),'Actual source target array is owned worker mutable BSS, runtime values separately observed')
   ref=pin(Path(build['preparation'])/'reference.cpp').read_text();need('Exact formatting caller return span'in ref and 'Original selected source changed after checkpoint'in ref and 'Formatting source restored'in ref,'Actual executed worker guards source-before installer and complete source-after conservation');reader.close();reader=None;counts['actual_original_workers']+=1
  need(counts['compiled_linked_functions']==12 and len(template)==6,'Complete both worker attribution');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader:reader.close()
  p=out/'compiled-observer-attribution.json';p.write_text(json.dumps(rows,indent=2)+'\n');pin(p);pin(__file__);report=dict(passed=passed,scope='Exact full compiled and final linked six formatter CPU/FX/ENV/cdecl wrappers in both genuine original workers, actual entry IAT targets and physical return-hook initializer targets. Original return hook runtime page is not separately captured; checked installer and source-restoration guards are bound. Independent review remains separate.',counts=dict(counts),actual_entry_IAT_targets_observed=True,return_hook_targets_from_actual_final_initializer=True,return_hook_runtime_page_observed=False,debugger_and_normal_compiled_wrapper_equality=True,allocator_generation_scope='Logical allocation occurrence index+1; no OS heap generation claim',whole_CPU40_FX512_ENV28_preservation=True,reader_closed=True,no_native_acceptance_credit=True,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
