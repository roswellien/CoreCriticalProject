"""Independent raw font/API ownership and exact unseeded stack liveness audit."""
from pathlib import Path
import ast,bisect,collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-startup138-original';P={};counts=collections.Counter();reader=None;passed=False
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or v==h;P[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
out=R/'reports/m4-138-validation-review/current-widget-policy-review-r1';assert not out.exists();out.mkdir()
try:
 sourcepath=B/'widget-complete-source-r1/report.json';source=read(sourcepath,'4f9e1d0a8fc80f4780bf9e6ce50fe5bf1df3dcc02b42581fa369fe0c6e889684');assert source['passed']and source['ordinary_raw_export_closed']and not source['AFTER_machine_or_memory_seed']and not source['source_shutdown_executed']and source['unused_API_stack_bytes_proven_unread_before_literal_overwrite']
 prep=read(B/'widget-complete-source-preparation-r1/report.json','d6f326884bcc0abafcfca970442963715c0469e0e8006d1c6b273bf568831f4e');assert prep['passed']and prep['exact_reverse_restores_parent_v4']
 tool=R/'tools/m4-startup138-original/compare_widget_complete_v5.py';text=pin(tool,source['files'][str(tool.resolve())]).read_text();reverse=text
 for d in reversed(prep['changes']):
  pos=d['position'];assert reverse[pos:pos+len(d['new'])]==d['new'];reverse=reverse[:pos]+d['old']+reverse[pos+len(d['new']):]
 assert reverse==pin(tool.with_name('compare_widget_source_v4.py')).read_text();ast.parse(text)
 helper=pin(tool.with_name('font_source_generations.py'),'b077343eca6ab980d2513796565c34a73a01fddfffead7a511f6e11ff876cdf9');assert 'manual_cleanup_is_source_callback=False' in helper.read_text()
 validationpath=B/'original-validation-r3/report.json';validation=read(validationpath,'02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f');assert validation['passed']and validation['reader_closed']and validation['paired_export_readers_closed']
 build=read(validation['build_path'],validation['build_sha256']);originalprep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);fixed=originalprep['observed_pages'];spec=pin(Path(build['preparation'])/'spec.hpp').read_text();whole=[int(x.strip(),16)for x in re.search(r'std::array<unsigned,69> widget_whole_pages\{([^}]+)\};',spec).group(1).split(',')];assert whole[:43]==fixed and len(set(whole))==69
 readerpath=pin(R/'tools/m4-startup131-original/export_reader.py');s=importlib.util.spec_from_file_location('widget_policy_ordinary',readerpath);E=importlib.util.module_from_spec(s);s.loader.exec_module(E);reader=E.ExportReader(validationpath,'02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f','original',pin)
 def sealed(name):return read(validationpath.parent/name,validation['files'][str((validationpath.parent/name).resolve())])
 gdifacts=sealed('widget-GDI-observations.json');FPS=sealed('FPS-observations.json');lifetime=sealed('font-resource-lifetimes.json')
 rows=read(sourcepath.parent/'source-derivations.json',source['files'][str((sourcepath.parent/'source-derivations.json').resolve())]);fonts=read(sourcepath.parent/'source-font-generations.json',source['files'][str((sourcepath.parent/'source-font-generations.json').resolve())]);assert len(rows)==42 and len(fonts)==90
 indexed={(r['sequence'],r['phase']):r for r in rows};assert len(indexed)==42
 for row in rows:
  seq,phase=row['sequence'],row['phase'];stem=f'phase/{seq}/{phase}/';access=row['source_accesses'];record=reader.data(f'phase/{seq}/{phase}.bin');stack=bytearray(record[2276+fixed.index(0x20001000)*4096:2276+(fixed.index(0x20001000)+1)*4096]);assert len(stack)==4096
  bybyte=collections.defaultdict(list)
  for i,a in enumerate(access):
   for address in range(max(0x20001000,a[1]),min(0x20002000,a[1]+a[3])):bybyte[address].append(i)
  blobs={};cursor=0
  for obs in sorted(row['unused_observed_API_stack_bytes'],key=lambda x:x['source_access_index']):
   end=obs['source_access_index'];assert 0<=end<=len(access)and not obs['value_seeded']
   while cursor<end:
    pc,address,value,width,write=access[cursor]
    if write:
     lo=max(address,0x20001000);hi=min(address+width,0x20002000)
     if lo<hi:stack[lo-0x20001000:hi-0x20001000]=value.to_bytes(width,'little')[lo-address:hi-address]
    cursor+=1
   assert stack[obs['address']-0x20001000]==obs['source_value']
   role='FPS'if obs.get('boundary_role')=='FPS'else'GDI';key='fps-snapshots.bin'if role=='FPS'else'widget-snapshots.bin';width=550180 if role=='FPS'else 287444
   if key not in blobs:blobs[key]=reader.data(stem+key)
   snapshot=blobs[key][obs['boundary_index']*width:(obs['boundary_index']+1)*width];assert len(snapshot)==width
   assert snapshot[4820+whole.index(0x20001000)*4096+obs['address']-0x20001000]==obs['actual_value']and obs['actual_value']!=obs['source_value']
   indexes=bybyte[obs['address']];i=bisect.bisect_left(indexes,end)
   if i<len(indexes):
    position=indexes[i];a=access[position];assert a[4]and obs['dominating_literal_store']==dict(index=position,PC=a[0],address=a[1],value=a[2],width=a[3]);counts['first_later_access_is_literal_store']+=1
   else:assert obs['never_subsequently_source_accessed'];counts['never_accessed_again_within_root']+=1
   counts['independent_raw_unseeded_stack_byte_relations']+=1
  ledger=reader.data(stem+'api-ledger.bin');words=list(struct.iter_unpack('<26I',ledger));assert len(words)==len(row['provider_API_joins'])
  for w,j in zip(words,row['provider_API_joins']):
   assert w[9]==w[19]==0 and w[24]==j['kind']and w[25]==j['return_word']and not j['actual_API_PC_observed']and j['source_target_bound_by_CALL_IAT_kind']and not j['memory_output_seed'];counts['raw_zeroPC_provider_API_joins']+=1
  for birth in row['source_registry_reallocation_inputs']:
   ai=birth['API_index'];w=words[ai];initial=reader.data(stem+f'api-initial/{ai}/bytes.bin');size=u(reader.data(stem+f'api-initial/{ai}/size.bin'))[0]
   assert w[24]==3 and w[25]==0x78011c2d and birth['source_CALL_pc']==0x78011c27 and birth['requested']==w[23]and birth['old_begin']==w[22]and birth['actual_pointer']==w[10]and birth['API_return_capacity']==size==len(initial)and birth['API_initial_backing_sha256']==hashlib.sha256(initial).hexdigest()and birth['complete_old_prefix_source_derived']and not birth['AFTER_endpoint_seed'];counts['independent_raw_registry_birth_relations']+=1
 for font in fonts:
  seq,phase=font['sequence'],font['phase'];row=indexed[seq,phase];store=font['source_owning_store'];assert row['source_accesses'][store['source_access_index']]==[0x5a0753,font['instance']+0x258,font['handle'],4,1]and store['address']==font['instance']+0x258 and store['value']==font['handle']
  after=next(f for f in gdifacts if f['sequence']==seq and f['phase']==phase and f['index']==font['created_event']);before=next(f for f in gdifacts if f['sequence']==seq and f['phase']==phase and f['index']==font['created_event']-1)
  assert after['API']==before['API']=='CreateFontA'and after['CPU'][0]==font['handle']and before['CPU'][6]==after['CPU'][6]==font['instance']
  counts['independent_same_instance_source_font_stores']+=1
  resources=reader.data(f'cleanup/{seq}/resources.bin');h=u(resources,font['occurrence']*32,8);assert h[:6]==(1,font['occurrence'],font['root'],font['instance'],font['handle'],font['created_event'])
  if font['live']:
   raw=reader.data(f'cleanup/{seq}/owned-font/{font["occurrence"]}.bin');assert len(raw)==1112 and u(raw,0,4)==h[:2]+h[3:5]and u(raw,16)[0]==font['manual_cleanup_BOOL']!=0 and u(raw,28)[0]==1 and h[6:]==(0,0xfffffffe)and raw[32:544]==raw[544:1056]and raw[1056:1084]==raw[1084:1112];counts['independent_typed_manual_owned_font_cleanup']+=1
  else:assert h[6:]==(0,font['deleted_event'])
  expected=next(x for x in lifetime if x['sequence']==seq and x['occurrence']==font['occurrence']);assert all(font.get(k)==v for k,v in expected.items())
 assert counts['independent_raw_unseeded_stack_byte_relations']==587198 and counts['independent_same_instance_source_font_stores']==90 and counts['independent_raw_registry_birth_relations']==12 and counts['raw_zeroPC_provider_API_joins']==150
 for p in('docs/m4-progress-startup131.md','docs/m4-startup-plan.md','tools/m4-fps-original/compare_source_v3.py','tools/m4-widget-source/compare_original_v6.py'):pin(R/p)
 pin(__file__);passed=True
except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
finally:
 if reader is not None:reader.close()
 q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Independent current original42-root source policy and exact raw unseeded stack/font/API ownership corroboration; native carried138/source pair/fault and root acceptance remain separate.',counts=dict(counts),manual_cleanup_policy='Typed owned-resource release evidence is admissible for initializer resource lifetime; it never proves compiled/source shutdown callback execution.',original_source_gate_finite42_supported=passed,whole_source_root_stack_equality_claim=False,stack_liveness_scope='Each literal root only; every mismatched actual API byte is unread before its next literal store or not read again in that root. Cross-root whole-stack source/native equality remains persistent/pair acceptance scope.',source_shutdown_executed=False,source_callback_cleanup_executed=False,original_API_PC_directly_observed=False,API_target_PC_source_derived_separately=True,AFTER_memory_seed=False,archive_reader_opened=False,ordinary_export_closed=reader is None or reader.closed,initializer_credit=0,files=P),indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest(),dict(counts),passed)
