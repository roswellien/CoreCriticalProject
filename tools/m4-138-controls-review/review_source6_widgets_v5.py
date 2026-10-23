"""Independent sealed widget source journal and physical GDI correspondence.

This does not independently replay literal byteflow or reauthenticate raw
identity observations. Their whole equality is owned by the sealed producer
and later dependency union; this review states that remaining gate explicitly.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
ROOTS=(0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0)
CALLBACKS=(0x40e420,0x40ef90,0x40f030,0x4795d0,0x5a3c60,0x5a4020,0x5a6720)
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive');v=sha(p);need(h is None or v==h,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable input');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main():
 p=Path(sys.argv[1]).resolve();out=R/'reports/m4-138-controls-review'/sys.argv[3];need(not out.exists(),'Fresh review');out.mkdir(parents=True);passed=False;counts=collections.Counter()
 try:
  r=read(p,sys.argv[2]);need(sha(p)=='40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052'and r['passed']and r['reader_closed'],'Exact complete source6')
  def output(n):
   q=p.parent/n;return read(q,r['files'][str(q.resolve())])
  rows=output('Widget-source-derivations.json');cleanup=output('Widget-manual-native-cleanup.json')
  need([(x['level'],x['sequence'],x['root'])for x in rows]==[(l,s,root)for l in('O0','O2')for s in range(6)for root in ROOTS],'Every and only ordered84 roots')
  need([(x['level'],x['sequence'])for x in cleanup]==[(l,s)for l in('O0','O2')for s in range(6)],'Every12 cleanups')
  module_path=R/'tools/m4-widget-growth-review/gdi_identity.py';spec=importlib.util.spec_from_file_location('independent_source6_physical_GDI',pin(module_path,r['files'][str(module_path.resolve())]));G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G);cache={};calls={}
  for c in cleanup:
   physical=c['physical_GDI'];case=c['level'],c['sequence'];need(c['actual_owned_font_frees']==15 and c['font_generations']==list(range(16,1,-1)) and c['whole_caller_FX512_ENV28_restore']is True and c['source_callbacks_executed']is False and c['AFTER_State_or_memory_seed']is False,'Exact15 manual reverse-generation frees; caller restoration/no source teardown')
   need(physical['passed']and physical['actual_source_calls']==149 and physical['actual_manual_calls']==15 and physical['whole_identity_sides']==physical['whole_named_entry64_sides']==328,'Whole source/manual physical extent')
   proofs={}
   for proof in physical['unique_named_provider_proofs']:
    path=pin(proof['actual_owner'],proof['physical_sha256']);key=str(path),proof['physical_sha256']
    if key not in cache:cache[key]=G.PhysicalPE(path.read_bytes())
    pe=cache[key];named=pe.exports[proof['requested']];need(named['forwarder']is None and named['rva']==proof['rva']==proof['target']-proof['owner'] and named['ordinal']==proof['ordinal'],'Measured target exact named final physical owning export')
    entry,relocs=pe.entry64(proof['rva'],proof['owner']);need(entry.hex()==proof['entry64'] and relocs==proof['DIR64_relocations'],'Whole relocated64 physical bytes')
    need(proof['matched_owning_export']==proof['requested']and proof['requested']in proof['same_rva_named_exports'],'Exact named correspondence')
    proofs[proof['requested'],str(path),proof['owner'],proof['target']]=proof;counts['physical_named_export_proofs']+=1
   for serial,a in enumerate(physical['calls']):
    w=a['call_words'];i=a['identity_words'];need(len(w)==11 and len(i)==9 and w[:2]==[1,serial]and i[:3]==[1,w[2],w[8]] and i[6]==0x1000 and i[8]==0x1000000,'Whole measured11Q/9Q identity type and target')
    need(i[3]<=i[4]<=i[2]and i[2]+64<=i[4]+i[5]and i[7]&255 in(0x10,0x20,0x40,0x80)and not i[7]&0x100,'Measured committed executable region contains whole entry64')
    need((a['requested'],a['physical_owner'],i[3],i[2])in proofs and a['rva']==i[2]-i[3]and w[9]==physical['host_thread'],'Actual call joins exact proof/thread')
    need(w[3]==int(serial>=149),'Exact source/manual ownership domain')
    calls[case+(serial,)]=a;counts['whole_measured_GDI_identity_call_joins']+=1
   need(len(physical['calls'])==164,'No missing/extra physical GDI calls')
  phases=output('phases.json');phase_map={(x['level'],x['sequence'],x['entry']):x for x in phases};phase_index={(x['level'],x['sequence'],x['phase']):x for x in phases};identities=output('API-identity-proofs.json')['observations'];API_map={(x['level'],x['sequence'],x['API_index']):x for x in identities}
  helper_path=pin(R/'tools/m4-138-controls-review/widget_growth_contract.py','b374b777ac667ce9d8790aadcbe057192d66794f7e85bac9a74438d254bd8406');spec=importlib.util.spec_from_file_location('independent_literal_widget_growth',helper_path);WG=importlib.util.module_from_spec(spec);spec.loader.exec_module(WG)
  model_path=R/'reports/m4-fps-original/source-preparation-r4/game_model.py';spec=importlib.util.spec_from_file_location('independent_widget_program',pin(model_path,r['files'][str(model_path.resolve())]));GM=importlib.util.module_from_spec(spec);spec.loader.exec_module(GM);program,_=GM.source_program()
  contract_path=R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json';contract=read(contract_path,r['files'][str(contract_path.resolve())])
  for d in contract['instructions']:
   if d['pc']in program:need(program[d['pc']]['bytes_hex']==d['bytes_hex']and program[d['pc']]['width']==d['width'],'Exact retained/additional provider literal descriptor')
   else:program[d['pc']]=d
  growth_results={}
  for x in rows:
   root=x['root'];b=x['borrowed_provider'];g=x['GDI_source'];component=x['component_source_accesses'];merged=x['source_accesses'];start=g['component_access_begin'];indexes=[v-start for v in b['shared_component_source_indices']]
   shared=[[0x5ac11e,0x5bb52c,0x1decb0,4,0],[0x5ac11e,0x200017e8,0x5ac124,4,1]]
   need(indexes==[len(component)-5,len(component)-4]and [component[i]for i in indexes]==b['shared_source_rows']==shared,'Exact two shared owning-IAT/CALL-frame operands')
   case=x['level'],x['sequence'];phase=phase_map[case+(root,)];first=phase_index[case+(phase['phase']-1,)]['finite_API_index'];last=phase['finite_API_index'];growth=WG.verify(x,[API_map[case+(i,)]for i in range(first,last)],program);counts['physically_discriminated_growth_intervals']+=int(growth['growth']);growth_results[case+(root,)]=growth
   need(b['provider_source_end']-b['provider_source_start']==growth['expected_provider_operands'] and b['provider_source_start']==b['provider_before_source_index']+2,'Exact independently discriminated complete borrowed source interval')
   need(merged==component[:indexes[-1]+1]+b['provider_source_rows']+component[indexes[-1]+1:],'Entire independent prefix/provider/tail journal union; no omitted/repeated operands')
   need(b['source_CALL_frame']==0x200017e8 and b['callback']==CALLBACKS[ROOTS.index(root)]and b['returned']is True and b['borrowed_projection']==[9,root,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,0x200017e8,0x5ac124],'Exact callback and literal CALL/RET source association')
   for side in('before','after'):need(len(bytes.fromhex(b[side+'_CPU_hex']))==40 and len(bytes.fromhex(b[side+'_FX_hex']))==512 and len(b[side+'_State_sha256'])==64,'Whole borrowed source State/CPU/FX record')
   need(x['whole_State_source_derived']is True and x['AFTER_machine_or_page_seed']is False and g['source_order_verified']and g['component_context_verified'],'Whole carried source derivation scope')
   for flag in('AFTER_State_or_memory_seed','guest_FX_transport','original_GDI_handle_seed','WG_global_access_indexes_used_for_witness_equality','source_callback_teardown_executed'):need(g[flag]is False,'Strict widget scope '+flag)
   for a in g['API_response_derivations']:
    observed=calls[x['level'],x['sequence'],a['serial']];w=observed['call_words'];need(observed['source_record_sha256']==a['API_record_sha256'] and w[4:9]==[root,a['CALL_pc'],a['source_frame'],a['instance'],a['native_target']]and w[9:]==[a['thread'],a['native_RAX']]and observed['requested']==a['service'],'Exact source response joins retained physical call record')
    need(a['full_guest_FX_unchanged']is True and a['native_full_call_argument_capture_claimed']is False,'Finite typed API and unchanged guestFX scope');counts['source_response_physical_call_joins']+=1
   counts['complete_widget_journal_unions']+=1;counts['whole_widget_source_operands']+=len(merged)
  need(counts['complete_widget_journal_unions']==84 and counts['source_response_physical_call_joins']==1788 and counts['whole_measured_GDI_identity_call_joins']==1968,'Exact full source journal/physical API extent')
  helper_path=pin(R/'tools/m4-138-controls-review/widget_byteflow.py','fef42aaf6566eca5788e076d3088a44f08d871df84547605eafb14ea615ff063');spec=importlib.util.spec_from_file_location('independent_whole_widget_memory',helper_path);BF=importlib.util.module_from_spec(spec);spec.loader.exec_module(BF)
  paired_path=R/'reports/m4-joint-startup138-source/preparation-r11/paired_exports.py';spec=importlib.util.spec_from_file_location('independent_widget_raw_equality_exports',pin(paired_path,r['files'][str(paired_path.resolve())]));EX=importlib.util.module_from_spec(spec);spec.loader.exec_module(EX);byteflows=[]
  for level in('O0','O2'):
   facade=EX.Facade(next(v for v in r['paired_exports']if v['branch']==level),pin)
   try:
    for seq in range(6):
     current=next(c for c in cleanup if(c['level'],c['sequence'])==(level,seq));prefix=f'sequence-{seq}/Widget/';manual=[];names=set()
     for generation in current['font_generations']:
      stem=prefix+'manual-font-cleanup/'+str(generation);manual.append((facade.data(stem+'-row.bin'),facade.data(stem+'-hardware.bin')));names.update((stem+'-row.bin',stem+'-hardware.bin'))
     need({name for name in facade.entries if name.startswith(prefix+'manual-font-cleanup/')}==names,'All and only15 complete actual owned font cleanup observations')
     source_records=facade.data(prefix+'root-'+str(ROOTS[-1])+'/after/APIs.bin')
     raw=G.verify(facade.data,pin,prefix=prefix,source_records=source_records,manual_records=manual,logical_names=facade.entries,expected_thread=current['physical_GDI']['host_thread'])
     need(json.loads(json.dumps(raw,sort_keys=True))==current['physical_GDI'],'Whole independently repeated raw physical identity/named export/source/manual proof correspondence')
     parsed=G.parse_source_records(source_records)
     for rootrow in rows:
      if(rootrow['level'],rootrow['sequence'])!=(level,seq):continue
      for response in rootrow['GDI_source']['API_response_derivations']:
       serial=response['serial'];record=source_records[serial*1488:(serial+1)*1488];argc=14 if response['service']=='CreateFontA'else 1
       need(hashlib.sha256(record).hexdigest()==response['API_record_sha256']and parsed[serial]['record_sha256']==response['API_record_sha256'],'Whole actual API1488 digest joins source response')
       need(list(struct.unpack_from('<14I',record,208)[:argc])==response['source_arguments'],'Every typed actual source argument DWORD joins source computation')
     counts['independently_authenticated_raw_GDI_calls']+=164;counts['independent_complete_raw_GDI_cases']+=1
    for row in rows:
     if row['level']!=level:continue
     key=level,row['sequence'],row['root'];proof=BF.verify(row,facade.data,phase_map[key]['phase']);growth=growth_results[key]
     need(proof['delegated_registry_callback_store']['address']==growth['callback_slot'],'Separately owned callback publication exact typed capacity/reallocation-derived slot')
     proof.update(level=level,sequence=row['sequence'],root=row['root'],literal_registry_ownership_and_capacity=growth);byteflows.append(proof);counts.update(proof['counts']);counts['independent_widget_memory_byteflows']+=1
   finally:facade.close()
  need(len(byteflows)==84,'Every complete current widget memory byteflow')
  artifact=out/'independent-widget-memory-byteflows.json';artifact.write_text(json.dumps(byteflows,indent=2)+'\n');pin(artifact)
  for q,h in list(PINS.items()):pin(q,h)
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,source_provider_path=str(p),source_provider_sha256=sha(p),scope='Independent84 entire merged journal associations and actual source-response/current final-owner physical named64-byte export correspondences from sealed ordinary records. Literal instruction byteflow and raw identity equality remain producing gate evidence.',counts=dict(counts),independent_component_memory_byteflow=passed,independent_current_registry_slot_capacity_derivation=passed,independent_full_literal_byteflow_replay=False,independent_raw_identity_equality=passed,full_source_widget_acceptance_closed=False,capture_archives_opened=0,worker_executed=False,reader_closed=True,initializer_credit=0,files=PINS)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main()
