"""Authenticate bounded genuine instruction observations; no numeric model."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-hypot-original';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def hw(b,o=0):return struct.unpack_from('<H',b,o)[0]
def cpu(c,pc=None):
 v=[u(c,i)[0]for i in(176,172,168,164,196,180,160,156,192,184)];v[8]&=~0x10100
 if pc is not None:v[9]=pc
 return v
def jcc(op,flags):
 cf,pf,zf,sf,of=[bool(flags&(1<<i))for i in(0,2,6,7,11)]
 return {'je':zf,'jz':zf,'jne':not zf,'jnz':not zf,'ja':not(cf or zf),'jae':not cf,'jb':cf,'jbe':cf or zf,'jg':not zf and sf==of,'jge':sf==of,'jl':sf!=of,'jle':zf or sf!=of,'jo':of,'jno':not of,'js':sf,'jns':not sf,'jp':pf,'jpe':pf,'jnp':not pf,'jpo':not pf}.get(op)
def main(path,digest,name):
 out=B/name;need(not out.exists(),'Fresh trace validation');out.mkdir();rawdir=out/'raw-observations';rawdir.mkdir();capture=None;passed=False;rows=[];accesses=[];counts=collections.Counter()
 try:
  execution=read(path,digest);need(execution['passed'],'Passed genuine trace writer');build=read(execution['build_path'],execution['build_sha256']);need(build['passed'],'Actual compiled trace worker');pin(build['worker'],build['worker_sha256']);prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(prep['trace_descriptors']==3538 and not prep['descriptor_gaps']and prep['SetThreadContext_written_sections']=='CONTEXT_CONTROL only'and not prep['debugger_FP_or_integer_sections_written']and not prep['normal_return_replay_used'],'Exact trace domain and observer writes')
  for p,h in prep['files'].items():pin(p,h)
  descriptors=read(Path(build['preparation'])/'trace-instruction-contracts.json')['instructions'];points={v['pc']:v for v in descriptors};imports=read(Path(build['preparation'])/'api-imports.json');normal=read(B/'prefix-validation-r2/report.json','80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313');normal_rows=read(B/'prefix-validation-r2/actual-hypot-endpoints.json',normal['files'][str((B/'prefix-validation-r2/actual-hypot-endpoints.json').resolve())]);pin(__file__);pin(sys.executable)
  s=importlib.util.spec_from_file_location('hypot_trace_actual_direct',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));D=importlib.util.module_from_spec(s);s.loader.exec_module(D);capture=D.DirectSet(Path(execution['original_capture']),pin);need(capture.data('COMPLETE.txt')==b'complete','Actual trace completion');need(u(capture.data('hypot/identity.bin'),0,4)==(0x5bb5b0,0x7802a122,0,0x78000000),'Actual named provider without normal wrapper')
  pages=prep['observed_pages']
  for seq in range(6):
   stem=f'phase/{seq}/0/';record=capture.data(f'phase/{seq}/0.bin');need(len(record)==356992 and u(record,0,9)[0]==seq and u(record,28,2)==(0,1),'Whole actual successful trace phase and outside caller host restoration');need(u(capture.data(stem+'hypot-count.bin'))==(0,),'No normal cdecl wrapper used in trace');normal_row=normal_rows[seq];own_before=cpu_from_record=u(record,36,10);own_after=u(record,76,10);need(own_before[9]==0x4b5910 and own_after[9]==0x410a80 and own_after[4]==own_before[4]+4,'True source root CALL/RET');need(record[1140:1652]==record[1652:2164]and record[2220:2248]==record[2248:2276],'Complete actual outside host FX/ENV restoration')
   # Raw debugger ENV metadata is retained below; canonical FIP/FDP is proven only by the separately bound normal observer, not this trace.
   schema=u(capture.data(stem+'hypot-trace/schema.bin'),0,8);need(schema[:4]==(1840,9800,60,716)and 0<schema[4]<=32768 and schema[5]<=256 and schema[6]and schema[7]==seq+1,'Actual schema/full stopped contexts/case epoch');event_data=capture.data(stem+'hypot-trace/events.bin');api_data=capture.data(stem+'hypot-trace/APIs.bin');targets=u(capture.data(stem+'hypot-trace/targets.bin'),0,len(imports));need(len(event_data)==schema[4]*1840 and len(api_data)==schema[5]*9800,'Complete actual trace byte extents');need(u(capture.data(stem+'hypot-trace/segments-ready.bin'))==(1,),'Genuine segment observations initialized');segments=capture.data(stem+'hypot-trace/segments.bin');need(len(segments)==60 and all(u(segments,i*20+4,2)==(0,0xffffffff)for i in range(3)),'Actual flat32 DS/ES/SS whole descriptors')
   sequence=[];cells_rows=[];by_pc=collections.Counter();gaps=[];previous=None
   for index in range(schema[4]):
    raw=event_data[index*1840:(index+1)*1840];h=u(raw,0,8);pc=h[1];need(pc in points and h[0]==index and h[3]==pc+1 and h[4]==points[pc]['opcode']and h[5]==len(points[pc]['cells'])and h[6],'Actual source PC/opcode/complete descriptor occurrence');point=points[pc];before=raw[32:748];after=raw[748:1464];bc=cpu(before,pc);ac=cpu(after);need(u(before,184)[0]==pc+1 and ac[9]==h[2],'Actual debugger context source projection');frame_before=raw[1704:1768];frame_after=raw[1768:1832];heads=u(raw,1832,2)
    if previous is not None:
     if previous['next_PC']==pc:need(previous['AFTER_CPU'][:9]==bc[:9],'Whole carried source GPR/architectural flag state between adjacent actual instructions')
     else:gaps.append(dict(previous_index=index-1,source_pc=previous['PC'],source_next=previous['next_PC'],resumed_pc=pc))
    local=[]
    for i,d in enumerate(point['cells']):
     cell=raw[1464+i*60:1524+i*60];fields=u(cell,0,7);address=(d['displacement']+sum(bc[r]*v for r,v in enumerate(d['coefficients']))+(schema[6]if d['segment']else 0))&0xffffffff;need(fields==(address,d['width'],d['read'],d['write'],d['segment'],1,1),'Complete actual source operand geometry and readable pre/post bytes');a=cell[28:28+d['width']];b=cell[44:44+d['width']]
     if not d['write']:need(a==b,'One genuine read-only source operand unchanged by its instruction')
     v=dict(sequence=seq,instruction_index=index,PC=pc,operand_index=i,address=address,width=d['width'],read=d['read'],write=d['write'],segment=d['segment'],before_hex=a.hex(),after_hex=b.hex());local.append(v);cells_rows.append(v);counts['complete_actual_source_operand_joins']+=1;counts['actual_source_read_operands']+=bool(d['read']);counts['actual_source_write_operands']+=bool(d['write'])
    op=point['mnemonic'];next_pc=h[2];condition=jcc(op,bc[8]);args=point['contract']['decoded_operands']
    if condition is not None:need(next_pc==(args[0]['value']if condition else pc+point['width']),'Genuine reached branch matches actual carried flags');counts['actual_flag_branch_relations']+=1
    elif op=='ret':need(len(local)==1 and next_pc==int.from_bytes(bytes.fromhex(local[0]['before_hex']),'little')and ac[4]==bc[4]+4+(args[0]['value']if args else 0),'Actual complete RET source stack/cleanup relation');counts['actual_RET_relations']+=1
    elif op in('call','jmp'):
     operand=args[0];target=operand.get('value')if operand['kind']=='immediate'else bc[('eax','ecx','edx','ebx','esp','ebp','esi','edi').index(operand['register'])]if operand['kind']=='register'else int.from_bytes(bytes.fromhex(next(v['before_hex']for v in local if v['read'])),'little');need(next_pc==target,'Actual direct/held/import control target');counts['actual_CALL_JMP_relations']+=1
     if op=='call':need(ac[4]==bc[4]-4 and any(v['address']==ac[4]and v['write']and v['after_hex']==(pc+point['width']).to_bytes(4,'little').hex()for v in local),'Literal actual CALL return publication')
    else:need(next_pc==pc+point['width']or(point.get('repeat')and next_pc==pc),'Actual physical fallthrough or one genuine REP iteration')
    previous=dict(PC=pc,next_PC=next_pc,AFTER_CPU=ac);sequence.append(dict(index=index,PC=pc,next_PC=next_pc,BEFORE_CPU=bc,AFTER_CPU=ac,source_flags_before_raw=u(before,192)[0],source_flags_after_raw=u(after,192)[0],FS_heads=list(heads),cell_count=h[5]));by_pc[pc]+=1;counts['actual_source_instructions']+=1;counts['whole_actual_stopped_CONTEXT_observations']+=2
   need(sequence[0]['PC']==0x4b5910 and sequence[-1]['next_PC']==0x410a80,'Complete actual root trace boundaries');api_rows=[];hypot_calls=[]
   for index in range(schema[5]):
    raw=api_data[index*9800:(index+1)*9800];h=u(raw,0,12);need(h[0]==index and h[4]<len(imports)and h[6]==1 and h[2]==targets[h[4]],'Exact actual resolved and balanced named API interval');entry=raw[48:764];after=raw[764:1480];frame=raw[1480:1544];returned_frame=raw[1544:1608];stack_entry=raw[1608:5704];stack_after=raw[5704:9800];ec=cpu(entry);ac=cpu(after);need(ec[9]==h[2]and ac[9]==h[3]and u(frame)[0]==h[3],'Genuine API target/caller return PC');need(frame==stack_entry[ec[4]-0x20001000:ec[4]-0x20001000+64]and returned_frame==stack_after[ac[4]-0x20001000:ac[4]-0x20001000+64],'Whole actual API frames join their complete live stacks');entry_info=imports[h[4]];row=dict(index=index,source_PC=h[1],target=h[2],return_PC=h[3],import_index=h[4],import_name=entry_info['name'],owning_IAT=entry_info['iat'],argc=h[5],returned=h[6],thread=h[7],LastError=list(h[8:10]),FS_heads=list(h[10:12]),ENTRY_CPU=ec,AFTER_CPU=ac,ENTRY_CONTEXT716_hex=entry.hex(),AFTER_CONTEXT716_hex=after.hex(),entry_frame64_hex=frame.hex(),returned_frame64_hex=returned_frame.hex(),entry_whole_stack_hex=stack_entry.hex(),returned_whole_stack_hex=stack_after.hex())
    if entry_info['iat']==0x5bb5b0:
     need(entry_info['name']=='_hypot'and h[2]==0x7802a122 and h[1]in(0x4b58b8,0x4b58e3)and ac[4]==ec[4]+4 and h[10]==h[11],'Actual hypot cdecl RET4 and balanced source FS');normal_entry=normal_row['calls'][2*len(hypot_calls)];normal_return=normal_row['calls'][2*len(hypot_calls)+1];need(frame[4:20].hex()==normal_entry['actual_F64_arguments_hex'],'Actual trace/untraced finite literal argument agreement');raw80=after[236:246].hex();need(raw80==normal_return['actual_return_raw80_hex'],'Actual traced/untraced finite raw80 result agreement; observation only');row.update(actual_F64_arguments_hex=frame[4:20].hex(),actual_return_raw80_hex=raw80,numerical_result_observed_only=True);hypot_calls.append(row);counts['actual_hypot_cdecl_intervals']+=1
    api_rows.append(row);counts['whole_actual_API_CONTEXT_frame_stack_boundaries']+=2
   need(len(hypot_calls)==2,'Two exhaustive actual hypot source calls eachcase');need(not gaps,'No unobserved external instruction interval in actual finite math path')
   def image(side,address,n):
    base=2276 if side=='before'else 178404;offset=base+pages.index(address&~4095)*4096+(address&4095);return record[offset:offset+n]
   need(image('after',0x60b2c8,36).hex()==normal_row['AFTER_object_hex'],'Whole genuine trace/untraced9F32 publication agreement; no expected numerical model')
   crt_before=capture.data(stem+f'hypot-CRT-before/{0x7803b000}.bin');crt_after=capture.data(stem+f'hypot-CRT-after/{0x7803b000}.bin');global_value=int.from_bytes(crt_before[0x738:0x73c],'little');counts['actual_root_phases']+=1;counts['whole_game9F32_trace_untraced_observation_relations']+=1;counts['actual_raw_final_ENV28_observations']+=1
   for suffix,blob in [('events',event_data),('APIs',api_data),('record',record)]:
    p=rawdir/f'case-{seq}-{suffix}.bin';p.write_bytes(blob);pin(p)
   accesses.extend(cells_rows);rows.append(dict(sequence=seq,header=list(u(record,0,9)),event_count=schema[4],API_count=schema[5],TEB=schema[6],trace_epoch=schema[7],whole_segments60_hex=segments.hex(),own_BEFORE_CPU=list(own_before),own_AFTER_CPU=list(own_after),own_BEFORE_FX512_hex=record[116:628].hex(),own_AFTER_FX512_hex=record[628:1140].hex(),own_BEFORE_ENV28_hex=record[2164:2192].hex(),own_AFTER_ENV28_hex=record[2192:2220].hex(),provider_7803B738_before=global_value,provider_7803B738_after=int.from_bytes(crt_after[0x738:0x73c],'little'),actual_reached_PC_counts={str(k):v for k,v in sorted(by_pc.items())},instructions=sequence,APIs=api_rows,unobserved_external_instruction_intervals=gaps,normal_results_are_observation_comparison_only=True))
  need(counts['actual_root_phases']==6 and counts['actual_hypot_cdecl_intervals']==12,'Complete genuine six-case trace extent');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if capture is not None:capture.close();capture.entries.clear();capture.bundles.clear();capture=None
  for name_,value in [('actual-source-traces.json',rows),('actual-source-accesses.json',accesses)]:
   p=out/name_;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
  report=dict(passed=passed,scope='Actual reached physical source/control/operand/true API observations only; no literal numeric model or native credit',execution_path=str(path),execution_sha256=digest,counts=dict(counts),reader_closed=True,source_after_seed=False,numerical_model_used=False,native_executed=False,source_native_equivalence=False,initializer_credit=0,debugger_write_sections='CONTROL only',TF_RF_projection_mask=0x10100,normal_numerical_results_are_observation_comparison_only=True,canonical_debugger_FIP_FDP_claimed=False,debugger_metadata_replaced=False,normal_canonical_ENV_gate_sha256='80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313',files=PINS);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
