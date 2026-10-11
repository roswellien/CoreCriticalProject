"""Physical finite normal widget/GDI/page prerequisites for future probes."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-widget-source'
sys.path.insert(0,str(R/'tools/m4-service-initializers'))
s=importlib.util.spec_from_file_location('widget_plan_recover',R/'tools/m4-onexit-batch-recovery/recover.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
PINS={}
def need(v,t):
 if not v:raise ValueError(t)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.zip','.mwb'),'No capture payload');a=sha(p);need(h is None or a==h,'Exact finite widget source plan input');PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=B/name;need(not out.exists(),'Fresh finite widget plan');out.mkdir(parents=True)
 game=M.Module(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
 d=read(B/'dispatch-r1/report.json','ee96052d75b9f459bcb1a96953e7130bbb98125c1d57c76fa7ed8ada9c415375');need(d['passed'],'Exact source target chain')
 graphs=read(B/'dispatch-r1/game-bound-graphs.json');rows={r['pc']:r for g in graphs.values()for r in g['instructions']}
 contracts=read(B/'lift-preparation-r1/instruction-contracts.json');cs={r['pc']:r for r in contracts['instructions']}
 # Derive every CreateFontA argument from literal post-cleanup instructions,
 # retaining their exact caller stack inputs instead of supplying a result.
 frame=0x10000;regs={'esp':frame-4};stack={frame+4*(i+1):v for i,v in enumerate((0x5e15dc,10,500,6,0,0,2))};trace=[]
 for pc in sorted(cs):
  if not 0x5a0718<=pc<0x5a074b:continue
  r=cs[pc];a=r['decoded_operands'];op=r['mnemonic']
  def val(x):
   if x['kind']=='immediate':return x['value']
   if x['kind']=='register':return regs[x['register']]
   need(x['kind']=='memory'and x['terms']==[{'register':'esp','scale':1}],'Exact source CreateFont stack operand');return stack[regs['esp']+x['displacement']]
  if op=='mov':need(a[0]['kind']=='register','Only exact argument register loads');regs[a[0]['register']]=val(a[1])
  elif op=='push':v=val(a[0]);regs['esp']-=4;stack[regs['esp']]=v
  elif op=='neg':need(a[0]['kind']=='register','Literal argument negation');regs[a[0]['register']]=(-val(a[0]))&0xffffffff
  else:raise ValueError('Unrecognized CreateFont argument source '+str(r))
  trace.append(dict(PC=pc,row=rows[pc],ESP_root_offset=regs['esp']-frame))
 args=[stack[regs['esp']+4*i]&0xffffffff for i in range(14)];need(args==[0xfffffff6,6,0,0,500,0,0,0,0,4,0,1,2,0x5e15dc],'Exact fourteen source CreateFontA normal arguments')
 def cstring(p):
  raw=bytearray()
  for n in range(128):
   byte=bytes.fromhex(game.data(p+n,1)['initial_hex']);raw+=byte
   if byte==b'\0':return dict(address=p,bytes=len(raw),hex=raw.hex(),text=raw[:-1].decode('ascii'),physical=game.data(p,len(raw)))
  raise ValueError('Bounded exact source input string')
 sdk=pin(Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/um/wingdi.h'));sdktext=sdk.read_text();need('#define OEM_FIXED_FONT      10'in sdktext and 'WINAPI CreateFontA('in sdktext and 'WINAPI GetStockObject('in sdktext and 'WINAPI DeleteObject('in sdktext,'Actual installed SDK named ABI/stock constant')
 api=[]
 for pc,slot,name,argc,source_arg in[(0x5a013c,0x5bb070,'GetStockObject',1,[10]),(0x5a063f,0x5bb074,'DeleteObject',1,['current instance +258 handle from prior actual stock/create return']),(0x5a074b,0x5bb068,'CreateFontA',14,args)]:
  need(rows[pc]['mnemonic']=='call'and slot in game.imports and game.imports[slot]['name']==name,'Actual source named GDI import')
  api.append(dict(PC=pc,CALL_row=rows[pc],slot=slot,raw_PE_IAT=game.data(slot,4),symbol=game.imports[slot],argc=argc,calling_convention='x86 stdcall source; actual native Windows ABI',source_arguments=source_arg,return_PC=pc+rows[pc]['size'],original_raw_API_CPU_required=True,whole_native_handle_retained_privately=True,opaque_handle_copied_as_pointer=False,identity_proof_required=True))
 parent=read(R/'reports/m4-startup130-original/preparation-r2/report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814');parent_pages=set(parent['observed_pages'])|set(parent['extra_whole_source_pages']);need(len(parent_pages)==46,'Current130 whole source page inventory')
 objects=[dict(root=r,base=b,extent=e,last_byte=b+e-1,source_bound_scope='Literal normal constructor field/array extent; genuine entire BEFORE/AFTER pages still required')for r,b,e in((0x40e250,0x5f4d78,0x7594),(0x40ef50,0x5fc838,0x7540),(0x5a3c30,0x731ac0,0x4660),(0x5a3ff0,0x736130,0x1f0),(0x5a66f0,0x736328,0x1f0))]
 widget_pages=set()
 for o in objects:widget_pages.update(range(o['base']&~4095,(o['last_byte']&~4095)+4096,4096))
 widget_pages.update((0x5bb000,0x5bc000,0x5cf000,0x5d0000,0x5e1000,0x638000));new_pages=sorted(widget_pages-parent_pages)
 for page in widget_pages:need(game.section(page) is not None,'Each actual admitted game static page')
 controls=[
  ('root_slot','wrong initializer table DWORD or wrong current root object'),
  ('code','single source byte/slot table byte changed before selected root'),
  ('vptr_source','same target with missing/foreign/stale current-instance source vptr token'),
  ('vptr_partial','partial overlapping store invalidates prior 32-bit source vptr token'),
  ('array_caller','correct constructor target reached from wrong caller site/frame'),
  ('array_base','wrong root-relative base or wrong current element ECX'),
  ('array_count','count beyond literal25/15/5 or callback/stride altered'),
  ('array_iteration','skipped/repeated iteration or wrong helper frame generation'),
  ('array_reverse','5AC24B failure unwind remains unsupported before any destructor dispatch'),
  ('font_registry','nonzero current6384E8 refuses dormant font lookup domain'),
  ('format_nonnull','nonnull text format refuses dormant vsprintf domain'),
  ('DF_segments','backward REP or nonflat DS/ES/SS refused before zeroing source object'),
  ('stock_identity','wrong named service/import/resource category or stock10 argument'),
  ('font_arguments','wrong one of fourteen exact CreateFontA frame args or changed full face string'),
  ('font_null','null CreateFontA result preserves genuine failure frontier; no success credit'),
  ('handle_alias','foreign/stale/expired or truncated native handle/refused cross-instance handle alias'),
  ('stock_borrowed','borrowed stock resource remains distinct from owned CreateFont resource'),
  ('delete_frame','wrong named DeleteObject target/source frame/actual source-field handle'),
  ('handle_private','mutated private resource generation/native handle/liveness or observer history'),
  ('owned_cleanup','cleanup only owned created resources; no source callback/unwind credit'),
  ('provider_FX','actual GDI API full CPU40/FX512/ENV28 observation and immediate/public host FP conservation'),
  ('pages','out-of-role extent, cross-page denied operand or changed source-readonly page'),
 ]
 plan=dict(roots=5,root_objects=objects,current_input_requirements=dict(font_registry=game.data(0x6384e8,4),font_registry_current_zero_required=True,null_format_current_call_frame_required=True,DS_ES_SS_base0=True,DF0=True,CreateFont_success_required=True,stock_nonnull_required_for_proposed_delete_count=True),source_strings=[cstring(0x5e14e4),cstring(0x5e15dc)],API_source_contracts=api,CreateFont_argument_derivation=trace,conditional_normal_counts=dict(array_ctor_calls=75,text_object_constructors=65,GetStockObject_calls=65,CreateFontA_calls=15,DeleteObject_calls_if_all_stock_nonnull=65,created_font_lifetimes=15,registrations=5),GDI_resource_policy=dict(stock_handle='genuine borrowed OEM_FIXED_FONT resource; exact source DeleteObject attempt/response measured, no owned deletion credit',font_handle='each genuine successful CreateFontA acquisition retains full native handle/current lifetime and mapped guest identity; normal owned cleanup required',CPU='Actual original API volatile values are finite observed responses; no whole volatile original/native equality claim',API_behavior='No synthetic stock handle, host font substitute, forced CreateFont success or fixed DeleteObject return'),page_inventory=dict(parent_whole_pages=sorted(parent_pages),widget_candidate_pages=sorted(widget_pages),new_pages=new_pages,prospective_combined_pages=sorted(parent_pages|widget_pages),fixed_inherited_record_pages=43,prospective_external_extra_pages=len(parent_pages|widget_pages)-43,CPU_after_offsets=[76,116],FX_before_offsets=[116,628],packed_record_bytes=356992,actual_whole_page_coverage_unmeasured=True),source_FS=dict(constructor_records=12,vector_helper_records=16,vector_helper_scope_table=0x5d0f68,reverse_helper_scope_table=0x5d0f58,source_invocation_frame_indices_required=True,source_handler_dispatch_admitted=False),required_negative_controls=[dict(id=k,refusal=v)for k,v in controls],future_proof_sequence=['Genuine bounded five-root prefix with actual GDI API images/frames/full handles, whole input/object pages and complete repeated FS/array/vptr observations','Independent literal source from genuine BEFORE and actual typed API responses; compare complete capacities/pages/CPU/FX/ENV and every virtual call/array frame','Actual Runtime-selected O0/O2 five-root fixture with genuine GDI operations and finite private generation controls, owned resource cleanup and whole retry proof','Independent compiled/link/source/interface/control review; integrate batch in next persistent startup count only after all fresh original/native/source/lifecycle gates pass'],original_executed=False,native_executed=False,initializer_credit=0)
 p=out/'normal-plan.json';p.write_text(json.dumps(plan,indent=2)+'\n');pin(p)
 for p in(Path(__file__),R/'tools/m4-onexit-batch-recovery/recover.py',R/'tools/m4-service-initializers/recover.py',R/'tools/analysis/pe.py'):pin(p)
 report=dict(passed=True,scope='Exact static finite widget API argument/page/resource/control prerequisites; hypothetical counts remain conditional until genuine observed inputs',counts=dict(roots=5,source_API_contracts=3,new_candidate_whole_pages=len(new_pages),prospective_whole_pages=len(parent_pages|widget_pages),negative_control_domains=len(controls),literal_CreateFont_arguments=len(args)),plan=str(out/'normal-plan.json'),plan_sha256=sha(out/'normal-plan.json'),files=PINS,original_executed=False,native_executed=False,initializer_credit=0)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])
