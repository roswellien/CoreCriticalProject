"""Before-only architectural input projection for additive native FDIV replay.

Original AFTER data is never an execution input. Separate debug API-return
observations are retained as ABI reference metadata, never service results.
"""
import argparse,hashlib,json,pathlib,struct
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv-replay'
SOURCE=ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1'
def sha(p):
 with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def need(v,m):
 if not v:raise ValueError(m)
def project(row,b):
 start=row['raw_offset_including_row_length']+4;r=b[start:start+row['raw_bytes_including_row_length']-4];t=row['tags'];need(not t['debug'],'Only direct original BEFORE can seed replay');before=r[108:148];cpu=list(struct.unpack('<10I',before));need(cpu[4]==t['writer_sp']and cpu[9]==0x78004254,'Actual BEFORE writer frame');original_w=cpu[4];cpu[4]=0x20001800
 fx=r[188:700];env=r[2236:2264];need(struct.unpack_from('<H',fx)[0]==t['cw']and struct.unpack_from('<H',fx,2)[0]==0 and fx[4]==0 and struct.unpack_from('<I',fx,24)[0]==0x1f80,'Measured empty masked BEFORE FP domain');need(struct.unpack_from('<H',env)[0]==t['cw']and struct.unpack_from('<H',env,4)[0]==0 and struct.unpack_from('<H',env,8)[0]==0xffff,'Actual BEFORE separate legacy domain')
 variable=91348+40*(t['stack_pages_before']+t['stack_pages_after']);stack=r[variable:variable+t['stack_bytes']];need(len(stack)==t['stack_bytes'],'Complete observed BEFORE stack extent');guest=bytearray([0xa5]*4096);mask=bytearray(4096);lo=t['stack_base'];hi=lo+t['stack_bytes'];copied=[]
 for i in range(4096):
  original=original_w-0x800+i
  if lo<=original<hi:guest[i]=stack[original-lo];mask[i]=1;copied.append(i)
 need(struct.unpack_from('<I',guest,0x800)[0]==0x10000100,'Observed authored original outer return');struct.pack_into('<I',guest,0x800,0x78004232)
 tags=struct.pack('<6I',t['id'],t['repeat'],t['cw'],original_w,lo,hi);payload=tags+struct.pack('<10I',*cpu)+fx+env+guest+mask;need(len(payload)==8796,'Exact before-only input layout')
 description={'original_id':t['id'],'original_W':original_w,'guest_W':0x20001800,'address_translation':'guest = original - original_W + 0x20001800','observed_original_stack_range':[lo,hi],'copied_guest_page_offsets':[min(copied),max(copied)+1],'authored_fill_byte':0xa5,'observed_mask_count':sum(mask),'outer_return_projection':{'guest_address':0x20001800,'original':0x10000100,'native':0x78004232,'bytes':4},'original_direct_row_offset':row['raw_offset_including_row_length'],'original_direct_row_sha256':row['raw_sha256'],'before_only_payload_sha256':hashlib.sha256(payload).hexdigest(),'architectural_seed_sources':{'CPU':'direct row bytes108..148; onlyESP address projection','FX512':'direct row bytes188..700 literal, including distinct rawFX metadata','ENV28':'direct row bytes2236..2264 literal legacy metadata representation','stack':'direct BEFORE stack only, explicit translation/mask and one outer-return-word projection'},'AFTER_used_as_native_input':False}
 return payload,description
def main(out):
 out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh private replay preparation required');files={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact replay preparation association '+str(p));files[str(p)]=v
 bind(SOURCE/'report.json','4d5b66e3b48a808b722b0b38e921d11a8e716b1fe06f79516364283c5f0261e6');bind(SOURCE/'pins.json','ace672f9f4689ea53980e4e9e8ecbb3b39fed3d17d534d7d36d9675e7e51fed5')
 for p,h in read(SOURCE/'pins.json')['files'].items():bind(p,h)
 raw=SOURCE/'original.bin';bind(raw,'cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2');b=raw.read_bytes();rows=read(SOURCE/'actual-rows.json')['rows'];need(len(rows)==48,'Complete actual original reference');inputs=bytearray(b'MW4FRIN1'+struct.pack('<4I',1,24,8796,4096));descriptions=[];boundaries=[]
 for i in range(24):
  need(rows[i]['tags']['id']==i and rows[i+24]['tags']['cw']==rows[i]['tags']['cw']and rows[i+24]['tags']['repeat']==rows[i]['tags']['repeat'],'Actual direct/debug reference association');payload,description=project(rows[i],b);inputs.extend(payload);descriptions.append(description);boundaries.append({'direct_original_id':i,'debug_original_id':i+24,'measurement_source':'Separate instrumented real32bit source-return CONTEXT, not direct architectural seed','actual_API_returns':[x['before']for x in rows[i+24]['debug_events']],'used_as_native_result_or_AFTER_oracle':False,'native_service_policy':'Unchanged accepted Registry performs own actual64bit lookups/query; preserves declared guestvolatile representative.'})
 contract=ROOT/'docs/m4-crt-fdiv-replay-contract.md';bind(contract);bind(__file__)
 native=ROOT/'reports/m4-crt-fdiv/native-build-r3/build.json';gate=read(native);bind(native);need(gate['passed'],'Accepted frozen native primary')
 for group in('sources','tools','artifacts'):
  for p,h in gate[group].items():bind(p,h)
 out.mkdir(parents=True);(out/'before-inputs.bin').write_bytes(inputs);bind(out/'before-inputs.bin');(out/'prepare-source.py').write_bytes(pathlib.Path(__file__).read_bytes());bind(out/'prepare-source.py');(out/'api-boundary-observations.json').write_text(json.dumps({'rows':boundaries},indent=2)+'\n');bind(out/'api-boundary-observations.json')
 report={'passed':True,'scope':'Before-only native replay preparation; native replay not yet built or executed','inputs_path':str(out/'before-inputs.bin'),'inputs_sha256':sha(out/'before-inputs.bin'),'original_reference_path':str(raw),'original_reference_sha256':sha(raw),'input_rows':24,'input_header_bytes':24,'input_record_bytes':8796,'input_offsets':{'tags6DWORD':0,'CPU40':24,'FX512':64,'ENV28':576,'guest_stack4096':604,'observed_stack_byte_mask4096':4700},'source_pack':'reports/m4-crt-fdiv/native-derived-r1/pack.bin','source_pack_sha256':'fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80','actual_before_source_provider':'Same exact pack: the original BEFORE provider pages differ only at two declared owning IAT cells containing actual32bit pointers; native retains raw source IAT words and uses accepted typed source-read routing.','original_before_projection_rows':descriptions,'State_policy':'Author fresh full3504 opaque State pattern per input row; project only observed32bit CPU/arithmeticflags, rawFX and legacyENV x87 metadata/eight x86 XMM/rawMMX alias storage. Empty logical FP values and nonobserved fields remain explicit authored storage. Capture whole before/after State and separate FX without reseeding across compiled calls.','guest_FS_policy':'Unchanged Runtime-owned guest FS7FFDE000 and flat DS/SS, distinct from real original host TEB; provider writer has noFS source dependency.','API_policy':'Measured original32bit boundary observation metadata is separate, not read by native executor as returned values. Actual native64bit APIs own issued guest tokens and queryBOOL.','comparison_policy':'Independent source model must validate whole native State/pages/events/routes. Explicit outerPC/ESP/token transport and two ABI-unspecified ECX high halves remain declared. Full real Windows API stack footprint/instrumentation/caller bytes are preserved raw and excluded from a fabricated whole-stack portable contract. No silent normalization.','native_model_or_equivalence_accepted':False,'original_executed_by_this_preparation':False,'native_executed':False,'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n');print(json.dumps({'passed':True,'before_only_rows':24,'bindings':len(files),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
