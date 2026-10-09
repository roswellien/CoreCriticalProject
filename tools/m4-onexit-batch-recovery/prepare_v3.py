"""Corrected exact-end additive detailed mode-1/ownership contract for static recovery-r1."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('onexit_source_recovery',Path(__file__).with_name('recover.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def main():
 out=Path(sys.argv[1]).resolve();base.require(out.parent==ROOT/'reports/m4-onexit-batch-recovery' and not out.exists(),'Fresh owned output')
 # Use the exact source-recovery path; previous r1 outputs remain immutable.
 saved=sys.argv;sys.argv=[str(Path(__file__).with_name('recover.py')),str(out)]
 try:base.main()
 finally:sys.argv=saved
 graphs=json.loads((out/'provider-graphs.json').read_text());rows={r['pc']:r for n in graphs.values()for r in n['instructions']}
 ranges=[dict(name=n,start=a,stop=b)for n,a,b in[
  ('msize_mode_dispatch',0x7800151D,0x78001553),('msize_epilogue_and_mode1_HeapSize',0x78001594,0x780015BF),
  ('realloc_mode_dispatch',0x780019F1,0x78001A43),('realloc_epilogue',0x78001B0C,0x78001B1B),
  ('realloc_mode1_HeapReAlloc_and_newmode_branch',0x78011C0A,0x78011C52)]]
 for span in ranges:
  seq=[rows[pc]for pc in sorted(rows)if span['start']<=pc<span['stop']]
  base.require(seq and seq[0]['pc']==span['start'] and seq[-1]['pc']+seq[-1]['size']==span['stop'],'Complete exact selected mode-1 span')
  span.update(instructions=seq,bytes=span['stop']-span['start'],sha256=hashlib.sha256(b''.join(bytes.fromhex(r['bytes'])for r in seq)).hexdigest())
 base.save(out/'mode1-selected-spans.json',dict(scope='Original conditional source, bounded mode1/newmode0/nonnullpositive-size registration growth only; other branches remain recorded dependencies',spans=ranges,
  source_domain_checks=[dict(pc=0x78001545,meaning='msize mode3 branch'),dict(pc=0x7800154E,meaning='msize mode2 branch; current mode1 takesJNE1551â†’15AA'),
   dict(pc=0x78001A31,meaning='realloc mode3 branch'),dict(pc=0x78001A3A,meaning='realloc mode2 branch; current mode1 takesJNE1A3Dâ†’11C0A'),
   dict(pc=0x78011C35,meaning='read actual _newmode; only establishedzero returnsnull directly'),dict(pc=0x78011C42,meaning='nonzero newmode callsactual newhandler; remains unsupported')]))
 inputs=json.loads((out/'registry-inputs.json').read_text());crt=base.Module(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL')
 specs=[dict(name='HeapSize',pc=0x780015B5,slot=0x7802E1DC,argc=3,args=['fullwidth privately owned heap','DWORDflags0','fullwidth privately owned live allocation'],result='Actual native SIZE_T. Size valuesmustfitoriginal32-bitresult; native SIZE_T(-1) mapsdocumentedfailure0xFFFFFFFF. Requested capacity is not an API result.'),
  dict(name='HeapReAlloc',pc=0x78011C27,slot=0x7802E0B4,argc=4,args=['same owned heap','DWORDflags0','owned old allocation','actual source roundedpositive size'],result='Actual native pointer/null. Successful relocation atomically advances private native backing/aliasownership and preserves old bytes; NULL retains original alias, pointer and contents.')]
 for api in specs:
  api.update(original_import=crt.imports[api['slot']],original_IAT=crt.data(api['slot'],4),original_stack_cleanup=4*api['argc'],
   preservation='Native provider return/LastError/export proof measured before/after; source State/FX and fullpointer ownership checked independently; no guestpointer is passed toWindows')
 base.save(out/'new-api-contracts.json',specs)
 plan=json.loads((out/'whole-batch-contract.json').read_text())
 plan.update(mode1_spans='mode1-selected-spans.json',new_api_contracts='new-api-contracts.json',
  source_callback_state='Each original root writes its own constructor/global state before registration. A callback is code-address data, not a native function pointer or accepted dispatch.',
  research_schedule='Execute original sentinel stores on the carried entry path or an explicitly recorded source fragment. Invoke actual tableproducer using a declared sourceCALL frame. Executing producer is required before registration; no hostpublication ofbegin/next.',
  alternate_table_inputs='The _onexit path is selected by source-established gamebegin=-1. Separately measured __dllonexit can use an owned malloc-established alternate table with explicit declared researchinitialization; any projection must be isolatedfrom architecturalsourceequivalence.',
  actual_failure_scope='Actual API null/HeapSizeerror may be observed. Authored faultinjection proves causalrefusal/retainedownership, not execution ofthe originalproviderfailurebranch. No forcedsuccessfulbridge.',
  fatal_producer_scope='InitialmallocNULL storesbegin=0 before CALL7801E2D4â†’_amsg_exit7800BADB. Refuse there until fullfatalterminationcontract; no successfulproducerRETcredit.',
  callback_dispatch_scope='Terminationsource dispatches reverse entries at78005560; onecallback4C49C0reaches1138conditionalinstructions/13unresolvedsites. This is not needed to prove registration but blocks fullprocess-exitcredit.')
 base.save(out/'whole-batch-contract.json',plan)
 report=json.loads((out/'report.json').read_text());report.pop('new_original_bytes',None)
 callbacks=json.loads((out/'callback-graphs.json').read_text());cbrows={r['pc']:r for n in callbacks.values()for r in n['instructions']}
 normal=json.loads((out/'game-normal-graphs.json').read_text());nrows={r['pc']:r for n in normal.values()for r in n['instructions']}
 report.update(callback_unique_instructions=len(cbrows),callback_unique_original_bytes=sum(r['size']for r in cbrows.values()),
  normal_unique_instructions=len(nrows),normal_unique_original_bytes=sum(r['size']for r in nrows.values()),
  selected_new_mode1_spans=len(ranges),selected_new_mode1_bytes=sum(r['bytes']for r in ranges),preparation_source=base.bind(Path(__file__).resolve()))
 report['artifacts']=[base.bind(p)for p in sorted(out.iterdir())if p.is_file()and p.name not in('report.json','pins.json')]
 base.save(out/'report.json',report)
 pinned=report['input_bindings']+[report['preparation_source']]+report['artifacts']+[base.bind(out/'report.json')]
 base.save(out/'pins.json',dict(files={a['path']:a['sha256']for a in pinned},scope='Private exact static preparation only'))
 print(json.dumps(dict(passed_static_recovery=True,final_report_sha256=base.sha(out/'report.json'),roots=26,callbacks=26,
  normal_unique_instructions=len(nrows),normal_unique_bytes=report['normal_unique_original_bytes'],callback_unique_instructions=len(cbrows),callback_unique_bytes=report['callback_unique_original_bytes'],new_mode1_bytes=report['selected_new_mode1_bytes'])))

if __name__=='__main__':main()
