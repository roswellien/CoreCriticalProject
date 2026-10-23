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
  for x in rows:
   root=x['root'];b=x['borrowed_provider'];g=x['GDI_source'];component=x['component_source_accesses'];merged=x['source_accesses'];start=g['component_access_begin'];indexes=[v-start for v in b['shared_component_source_indices']]
   shared=[[0x5ac11e,0x5bb52c,0x1decb0,4,0],[0x5ac11e,0x200017e8,0x5ac124,4,1]]
   need(indexes==[len(component)-5,len(component)-4]and [component[i]for i in indexes]==b['shared_source_rows']==shared,'Exact two shared owning-IAT/CALL-frame operands')
   need(len(b['provider_source_rows'])==67 and b['provider_source_end']-b['provider_source_start']==67 and b['provider_source_start']==b['provider_before_source_index']+2,'Exact complete borrowed67 operand interval')
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
  for q,h in list(PINS.items()):pin(q,h)
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,source_provider_path=str(p),source_provider_sha256=sha(p),scope='Independent84 entire merged journal associations and actual source-response/current final-owner physical named64-byte export correspondences from sealed ordinary records. Literal instruction byteflow and raw identity equality remain producing gate evidence.',counts=dict(counts),independent_full_literal_byteflow_replay=False,independent_raw_identity_equality=False,full_source_widget_acceptance_closed=False,capture_archives_opened=0,worker_executed=False,reader_closed=True,initializer_credit=0,files=PINS)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main()
