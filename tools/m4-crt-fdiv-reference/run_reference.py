"""Bounded exact-source FDIV original capture runner and lossless row splitter.

--plan saves the concrete recipe without starting the worker. --execute is used
only after the separately completed scaffold review authorizes first capture.
This parses observed outcomes; it supplies no provider computational oracle.
"""
import argparse,hashlib,json,pathlib,re,struct,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv-reference'
EXPECTED={
 'review':'5a4636904248a43f1fd95a9f4c24cb9b268c507bdf811273e993c2ffa2aee315',
 'pins':'d102a95d3b7da367b8f9ce306d97504a985b44596269ad86dab506d40e9c6d9c',
 'build':'75aebc9be6f078be70f43f57269f1c28dfe4f20d014c0ac7236484d80d983fdc',
 'worker':'9066d65db5865990b0a00f1c512d61add0c6b8bb096e8a18f13f9cd5e141a2d3',
 'pack':'fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80',
 'provider':'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
}
PATHS={'review':BASE/'static-scaffold-review-r2/report.json','pins':BASE/'static-scaffold-review-r2/pins.json','build':BASE/'build-r3/build.json','worker':ROOT/'build/m4-crt-fdiv-reference-build-r3/Release/fdiv_reference.exe','pack':BASE/'preparation-r2/pack.bin','provider':ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'}
def sha(p):
 with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(p,value):
 with pathlib.Path(p).open('x',encoding='utf-8')as f:f.write(json.dumps(value,indent=2)+'\n')
def blob(p,b):
 with pathlib.Path(p).open('xb')as f:f.write(b)
def admit():
 for k,p in PATHS.items():need(sha(p)==EXPECTED[k],'Exact reviewed pre-call association '+k)
 m=read(PATHS['pins']);need(len(m['files'])==551,'Reviewed static binding extent')
 for p,h in m['files'].items():need(sha(p)==h,'Frozen physical pre-call binding '+p)
 b=read(PATHS['build']);need(b['passed']and not b['original_executed']and str(pathlib.Path(b['worker']).resolve())==str(PATHS['worker']),'Actual exact build-only identity')
 for group in('source_files','tool_files','compiler_read_headers','artifacts'):
  for p,h in b[group].items():need(sha(p)==h,'Frozen build binding '+p)
 return {'exact_named_files':{str(p):EXPECTED[k]for k,p in PATHS.items()},'review_physical_bindings':len(m['files']),'runner_path':str(pathlib.Path(__file__).resolve()),'runner_sha256':sha(__file__)}
TAGS=['id','repeat','debug','cw','status','debug_count','debug_unexpected','stack_base','stack_bytes','writer_sp','limit_before','base_before','limit_after','base_after','thread_id','teb','worker_base','context_bytes','stack_pages_before','stack_pages_after','source_api_module','source_api_proc','expected_module','expected_feature','snapshot_complete','restore_checkpoint','entry_complete']
REGIONS=[0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000]
PERMISSIONS=[0x20,0x20,0x20,2,2,2,4]
RETURNS=[0x780042ae,0x780042c2,0x780042ce]
def u32(b,p):return struct.unpack_from('<I',b,p)[0]
def cpu(b,p):return dict(zip(['eax','ecx','edx','ebx','esp','ebp','esi','edi','flags_image','pc'],struct.unpack_from('<10I',b,p)))
def host_region(b,p):return dict(zip(['base','bytes','allocation','state','type','protect','allocation_protect'],struct.unpack_from('<3Q4I',b,p)))
def context(b,p):
 return {name:u32(b,p+offset)for name,offset in [('context_flags',0),('dr0',4),('dr1',8),('dr2',12),('dr3',16),('dr6',20),('dr7',24),('edi',156),('esi',160),('ebx',164),('edx',168),('ecx',172),('eax',176),('ebp',180),('eip',184),('eflags',192),('esp',196)]}
def parse(raw,out):
 b=raw.read_bytes();need(len(b)>=32 and b[:8]==b'MW4FDOR1','Observed original raw header')
 need(struct.unpack_from('<6I',b,8)==(1,48,91348,716,80,1048576),'Exact compiled observed schema')
 off=32;rows=[];partitions=[bytearray(),bytearray()];pack=PATHS['pack'].read_bytes()
 for i in range(48):
  need(off+4<=len(b),'Observed row extent');n=u32(b,off);start=off+4;end=start+n;need(n>=91348 and end<=len(b),'Observed row payload bound');r=b[start:end];t=dict(zip(TAGS,struct.unpack_from('<27I',r,0)));before=cpu(r,108);after=cpu(r,148)
  need(t['id']==i and t['debug']==i//24 and t['repeat']==(i%24)//12 and t['cw']==[0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f][i%12],'Actual original declared corpus ordering')
  need(t['status']==0 and t['snapshot_complete']==t['entry_complete']==t['restore_checkpoint']==1,'Actual complete source/capture checkpoint outcome')
  need(t['worker_base']==0x34000000 and t['context_bytes']==716,'Actual loaded worker/CONTEXT proof')
  need(t['limit_before']==t['limit_after']==t['stack_base']and t['base_before']==t['base_after']==t['stack_base']+t['stack_bytes']and 0<t['stack_bytes']<=1048576 and not(t['stack_base']&4095) and not(t['stack_bytes']&4095),'Actual stable bounded stack extent')
  need(t['stack_pages_before']==t['stack_pages_after']==t['stack_bytes']//4096,'Full observed stack page count')
  variable=91348+40*(t['stack_pages_before']+t['stack_pages_after']);need(n==variable+2*t['stack_bytes'],'Exact full observed row extent')
  need(before['pc']==0x78004254 and before['esp']==t['writer_sp']and after['pc']==0x10000100 and after['esp']==before['esp']+4,'Actual natural original outer frame capture')
  need(t['stack_base']<=t['writer_sp']-256 and t['writer_sp']+4<t['base_before'],'Actual W and bounded source frame')
  regions=[]
  for phase,base in [('before',90708),('after',90988)]:
   for j,a in enumerate(REGIONS):
    v=host_region(r,base+40*j);need(v['allocation']==(a&~0xffff)and v['state']==0x1000 and v['type']==0x20000 and v['protect']==PERMISSIONS[j]and v['base']<=a and a+4096<=v['base']+v['bytes'],'Actual source private allocation/protection '+phase);regions.append({'phase':phase,'page':a,**v})
  stack_regions=[];allocation=None
  for phase,pages,base in [('before',t['stack_pages_before'],91348),('after',t['stack_pages_after'],91348+40*t['stack_pages_before'])]:
   for j in range(pages):
    address=t['stack_base']+4096*j;v=host_region(r,base+40*j);need(v['state']==0x1000 and v['type']==0x20000 and v['protect']==4 and v['base']<=address and address+4096<=v['base']+v['bytes'],'Actual captured stack page RW admission')
    if allocation is None:allocation=v['allocation']
    need(v['allocation']==allocation,'One actual thread stack allocation');stack_regions.append({'phase':phase,'page':address,**v})
  guards=[host_region(r,91268),host_region(r,91308)]
  need(all(v['state']==0x2000 or v['protect']&0x100 for v in guards),'Actual excluded guard/reserved boundary')
  before_pages=r[2348:31020];after_pages=r[31020:59692]
  expected=bytearray().join(pack[20+j*4104:20+j*4104+4096]for j in range(7));struct.pack_into('<I',expected,3*4096+0x98,t['source_api_module']);struct.pack_into('<I',expected,3*4096+0xd0,t['source_api_proc'])
  need(before_pages==expected,'Actual raw source pages match pack plus exactly two real IAT pointers');need(before_pages[:6*4096]==after_pages[:6*4096],'Actual RX/RO/IAT immutability')
  actual_debug=[];need(t['debug_unexpected']==0 and t['debug_count']==(3 if t['debug']else 0),'Actual separately observed debug event extent')
  for j in range(t['debug_count']):
   p=59692+j*1520;cb=p+88;ca=p+804;c=context(r,cb);continued=context(r,ca)
   need(u32(r,p)==j and u32(r,p+4)==t['thread_id']and u32(r,p+8)==0x80000004 and u32(r,p+20)==RETURNS[j]and c['eip']==RETURNS[j],'Actual source return breakpoint observation')
   need((c['context_flags']&0x10013)==0x10013 and c['dr6']&15==1<<j and not(c['eflags']&0x100),'Actual valid context/control/integer/debug flags')
   original_context=r[cb:cb+716];expected_context=bytearray(original_context);struct.pack_into('<I',expected_context,20,c['dr6']&~15);struct.pack_into('<I',expected_context,192,c['eflags']|0x10000);need(r[ca:ca+716]==expected_context,'Only explicit recorded RF/DR6 intervention')
   need(c['esp']==t['writer_sp']-4,'Actual source stdcall4/8/4 return cleanup')
   actual_debug.append({'ordinal':j,'before':c,'continued':continued,'original_CONTEXT_sha256':hashlib.sha256(original_context).hexdigest(),'FP_context_present':bool(c['context_flags']&8),'extended_FP_context_present':bool(c['context_flags']&32),'FP_context_is_direct_FNSTENV':False})
  value=u32(after_pages,6*4096+0xc2c)
  if t['debug']:need(actual_debug[0]['before']['eax']==t['expected_module']and actual_debug[1]['before']['eax']==t['expected_feature']and actual_debug[2]['before']['eax']==value,'Actual32bit dynamic return targets and source-written BOOL')
  memory_before=r[variable:variable+t['stack_bytes']];memory_after=r[variable+t['stack_bytes']:]
  need(u32(memory_before,t['writer_sp']-t['stack_base'])==0x10000100,'Actual authored outer return word in real stack')
  residual=[]
  for delta in(-34,-42):
   k=t['writer_sp']+delta-t['stack_base'];residual.append({'source_address':t['writer_sp']+delta,'before_hex':memory_before[k:k+2].hex(),'after_hex':memory_after[k:k+2].hex(),'ABI_unspecified_service_ECX_high_half':True})
  partitions[t['debug']].extend(b[off:end])
  row={'tags':t,'before_CPU':before,'after_CPU':after,'source_written_adjust_fdiv':value,'observed_FX_CW_before_after':[struct.unpack_from('<H',r,p)[0]for p in(188,700)],'observed_FX_SW_before_after':[struct.unpack_from('<H',r,p+2)[0]for p in(188,700)],'observed_ENV_CW_before_after':[struct.unpack_from('<H',r,p)[0]for p in(2236,2264)],'observed_ENV_SW_before_after':[struct.unpack_from('<H',r,p+4)[0]for p in(2236,2264)],'raw_offset_including_row_length':off,'raw_bytes_including_row_length':4+n,'raw_sha256':hashlib.sha256(b[off:end]).hexdigest(),'actual_source_regions':regions,'actual_stack_regions':stack_regions,'excluded_guard_regions':guards,'debug_events':actual_debug,'residual_service_ECX_halves':residual,'whole_stack_before_sha256':hashlib.sha256(memory_before).hexdigest(),'whole_stack_after_sha256':hashlib.sha256(memory_after).hexdigest(),'debug_off_per_service_volatiles_observed':False}
  rows.append(row);off=end
 need(b[off:]==b'COMPLETE','Actual terminal complete marker and no trailing data')
 for index,name in enumerate(('direct-original-rows.bin','debug-original-rows.bin')):blob(out/name,partitions[index])
 save(out/'actual-rows.json',{'rows':rows,'partitions':{'direct_original':str(out/'direct-original-rows.bin'),'debug_original':str(out/'debug-original-rows.bin')},'partition_encoding':'Byte-exact complete DWORD row_length plus raw row payload concatenation in original order; primary header/footer retained only in original.bin. No row bytes or values changed.','original_primary_sha256':sha(raw)})
 return rows
def main(output,execute):
 output=pathlib.Path(output).resolve();need(output.parent==BASE and not output.exists()and re.fullmatch('[a-z][a-z0-9-]{0,63}',output.name),'Fresh immediate ignored reference report directory')
 need('/reports/'in(ROOT/'.gitignore').read_text().splitlines(),'Private evidence directory must remain ignored')
 association=admit();output.mkdir();raw=output/'original.bin';command=[str(PATHS['worker']),str(PATHS['pack']),str(PATHS['provider']),str(raw)]
 recipe={'scope':'Bounded complete original32bit FDIV writer with natural Windows thread stack; no full DLL/CRT/game execution','execute_requested':execute,'original_executed':False,'command':command,'shell':False,'internal_broker_argument':'--pre-reserved inserted only by reviewed broker into exact executable/OS argument tail','broker_timeout_seconds':180,'runner_timeout_seconds':200,'pre_call_association':association,'corpus':{'rows':48,'debug_off':24,'debug_on':24,'CW_domain':'12 normalized masked IC0 words, empty TOP0/SW0','raw_primary':str(raw)},'source_IAT_transport':'Exactly two private owning IAT cells become actual32bit GetModuleHandleA/GetProcAddress addresses; returned FARPROC unchanged, source uses natural stdcall4/8/4 frames.','debug_transport':'Hardware execute return breakpoints only on24 debug-on rows; raw OS contexts retain actual PC/DR/RF/TF and explicit RF/DR6 intervention.','success_evidence':'Actual raw loaded worker base and private source/stack page identities; actual broker child PID/exit log; exact executed successful reservation admission checks are distinct from serialized VirtualQuery observations. Capture reservation has executed broker/stub admission and return evidence, no fabricated serialized sample.','output_policy':'CREATE_NEW fresh original output; failed observed prefix retained; COMPLETE only after48 accepted rows. Split files retain every raw row byte, without normalized fields.','whole_M4_complete':False}
 save(output/'launch-recipe.json',recipe);blob(output/'runner-source.py',pathlib.Path(__file__).read_bytes())
 if not execute:
  print(json.dumps({'planned_only':True,'command':command,'recipe_sha256':sha(output/'launch-recipe.json'),'runner_sha256':sha(__file__)}));return
 commands=[]
 try:
  # Recheck after publication of the recipe, immediately before Popen.
  need(admit()==association,'Pre-call associations unchanged')
  cp=subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,timeout=200,creationflags=subprocess.CREATE_NO_WINDOW)
  blob(output/'positive.stdout',cp.stdout);blob(output/'positive.stderr',cp.stderr)
  commands.append({'command':command,'exit_code':cp.returncode,'stdout':str(output/'positive.stdout'),'stderr':str(output/'positive.stderr')})
  need(cp.returncode==0,'Actual original worker failed; observed prefix/log retained')
  matches=re.findall(r'Original broker child finished: pid=(\d+) exit=(\d+)',cp.stderr.decode('utf-8','replace'));need(len(matches)==1 and int(matches[0][1])==0,'Actual broker child completion diagnostic')
  need('Actual child collision:'not in cp.stderr.decode('utf-8','replace'),'Actual pre-CRT collision cannot become source success')
  need(admit()==association,'Frozen associations remain exact after call');rows=parse(raw,output)
  report={'passed':True,'scope':'Actual original-only complete FDIV writer observations; native equivalence and full CRT/M4 remain open','original_executed':True,'native_executed':False,'records':len(rows),'debug_off_records':24,'debug_on_records':24,'raw':{'path':str(raw),'sha256':sha(raw),'bytes':raw.stat().st_size},'broker_child_pid':int(matches[0][0]),'broker_child_exit':0,'loaded_worker_base_observed':list(sorted({r['tags']['worker_base']for r in rows})),'source_private_allocations_observed':[0x78000000,0x78010000,0x78020000,0x78030000],'successful_pre_CRT_reservation_serialized_samples':False,'reservation_proof_scope':'Actual exact broker child exit/collision-free logs plus executed reviewed admission checks; raw source page allocation/protection proof. Capture reservation separate executed broker/stub admission and natural return, without serialized region sample.','source_written_BOOL_observations':list(sorted({r['source_written_adjust_fdiv']for r in rows})),'debug_off_context_or_API_volatile_guess':False,'debug_on_interventions_and_FP_metadata_separate':True,'normalization_performed':False,'pre_call_association':association,'commands':commands,'whole_M4_complete':False}
  save(output/'report.json',report)
 except subprocess.TimeoutExpired as e:
  blob(output/'timeout.stdout',e.stdout or b'');blob(output/'timeout.stderr',e.stderr or b'');save(output/'failure.json',{'passed':False,'reason':'Actual bounded200s runner timeout; parent killed and broker job ownership closes','original_may_have_executed':True,'raw_prefix_retained':raw.exists(),'pre_call_association':association,'commands':commands});raise
 except Exception as e:
  save(output/'failure.json',{'passed':False,'reason':str(e),'original_may_have_executed':True,'raw_prefix_retained':raw.exists(),'pre_call_association':association,'commands':commands});raise
 finally:
  files={str(p.resolve()):sha(p)for p in output.rglob('*')if p.is_file()};files[str(pathlib.Path(__file__).resolve())]=sha(__file__);files.update(association['exact_named_files']);save(output/'pins.json',{'files':files})
 print(json.dumps({'passed':True,'records':48,'report_sha256':sha(output/'report.json'),'pins_sha256':sha(output/'pins.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--plan',action='store_true');g.add_argument('--execute',action='store_true');a=p.parse_args();main(a.output,a.execute)
